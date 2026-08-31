import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date

st.set_page_config(page_title="Plataforma Educativa", page_icon="🎓", layout="wide")

CARPETA_ENTREGAS = "entregas_alumnos"
os.makedirs(CARPETA_ENTREGAS, exist_ok=True)

# --- ESTILOS CSS CON TEMA EDUCATIVO PROFESIONAL ---
st.markdown("""
<style>
    .stApp {
        background-color: #f3f6fa !important;
        background-image: linear-gradient(180deg, #edf2f7 0%, #f7f9fc 100%);
        color: #1e293b !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #0f172a !important;
    }
    .brand-title {
        font-size: 26px;
        font-weight: 800;
        color: #1b3a6b !important;
        letter-spacing: -0.5px;
    }
    .brand-badge {
        font-size: 13px;
        font-weight: 600;
        color: #0369a1 !important;
        background: #e0f2fe;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        margin-top: 2px;
    }
    .stButton > button {
        background-color: #1b3a6b !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #0f2444 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(27, 58, 107, 0.25);
    }
    .course-card {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 16px;
    }
    .card-banner-1 { height: 110px; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); }
    .card-banner-2 { height: 110px; background: linear-gradient(135deg, #065f46 0%, #10b981 100%); }
    .card-banner-3 { height: 110px; background: linear-gradient(135deg, #701a75 0%, #d946ef 100%); }
    .card-banner-4 { height: 110px; background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%); }
    .course-card-body { padding: 16px; background: #ffffff !important; }
    .course-title { font-size: 17px; font-weight: 700; color: #1e3a8a !important; margin-bottom: 4px; }
    .course-cat { font-size: 13px; color: #64748b !important; }
    .timer-box {
        background: #be123c;
        color: white !important;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 22px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(190, 18, 60, 0.2);
    }
    .q-correct { background-color: #dcfce7; border-left: 5px solid #16a34a; padding: 12px; margin-bottom: 10px; border-radius: 6px; color: #14532d !important; }
    .q-wrong { background-color: #ffe4e6; border-left: 5px solid #e11d48; padding: 12px; margin-bottom: 10px; border-radius: 6px; color: #881337 !important; }
    .task-response-box { background-color: #f1f5f9; border-left: 5px solid #1b3a6b; padding: 14px; border-radius: 6px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS LOCAL ---
conn = sqlite3.connect("campus_moodle.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    nombre TEXT,
    email TEXT,
    rol TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS catedras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    codigo TEXT UNIQUE,
    categoria TEXT DEFAULT 'Categoría 1',
    profesor_id INTEGER,
    FOREIGN KEY(profesor_id) REFERENCES usuarios(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS secciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catedra_id INTEGER,
    titulo TEXT,
    orden INTEGER,
    FOREIGN KEY(catedra_id) REFERENCES catedras(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS actividades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catedra_id INTEGER,
    seccion_id INTEGER,
    titulo TEXT,
    tipo TEXT,
    fecha_limite TEXT,
    duracion_minutos INTEGER DEFAULT 0,
    preguntas_json TEXT,
    descripcion TEXT,
    enlace_archivo TEXT,
    FOREIGN KEY(catedra_id) REFERENCES catedras(id),
    FOREIGN KEY(seccion_id) REFERENCES secciones(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS matriculas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catedra_id INTEGER,
    estudiante_id INTEGER,
    UNIQUE(catedra_id, estudiante_id),
    FOREIGN KEY(catedra_id) REFERENCES catedras(id),
    FOREIGN KEY(estudiante_id) REFERENCES usuarios(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS entregas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actividad_id INTEGER,
    estudiante_id INTEGER,
    fecha_entrega TEXT,
    respuesta_data TEXT,
    archivo_ruta TEXT,
    nota REAL,
    devolucion TEXT,
    tiempo_empleado_seg INTEGER,
    UNIQUE(actividad_id, estudiante_id),
    FOREIGN KEY(actividad_id) REFERENCES actividades(id),
    FOREIGN KEY(estudiante_id) REFERENCES usuarios(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT
)
""")
conn.commit()

# --- FUNCIONES DE EMAIL ---
def get_config(clave, default=""):
    r = c.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
    return r[0] if r else default

def set_config(clave, valor):
    c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", (clave, valor))
    conn.commit()

def enviar_credenciales_alumno(destinatario, nombre_alumno, curso_nombre, usuario, clave):
    remitente = get_config("smtp_email", "")
    smtp_pass = get_config("smtp_password", "")
    
    if not remitente or not smtp_pass:
        return False, "Credenciales SMTP no configuradas en el panel docente."

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Plataforma Educativa <{remitente}>"
        msg['To'] = destinatario
        msg['Subject'] = f"🎓 Acceso a tu curso: {curso_nombre}"

        cuerpo = f"""Hola {nombre_alumno},

Has sido matriculado/a exitosamente en el curso: {curso_nombre}

Tus credenciales de acceso son:
------------------------------------------
👤 Usuario: {usuario}
🔑 Contraseña: {clave}
------------------------------------------

Podés ingresar desde el navegador de tu computadora o celular.

Saludos cordiales,
Equipo Docente - Plataforma Educativa
Created by Tec. Cristian Nuñez
"""
        msg.attach(MIMEText(cuerpo, 'plain'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(remitente, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True, "Correo enviado correctamente."
    except Exception as e:
        return False, f"Error al enviar correo: {str(e)}"

# --- USUARIOS INICIALES ---
if c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
    c.execute("INSERT INTO usuarios (username, password, nombre, email, rol) VALUES ('profesor', '1234', 'Prof. Cristian Nuñez', 'prof@educacion.edu', 'profesor')")
    c.execute("INSERT INTO usuarios (username, password, nombre, email, rol) VALUES ('alumno1', '1234', 'Juan Pérez', 'juan@gmail.com', 'estudiante')")
    conn.commit()

# --- SESIÓN ---
if "user" not in st.session_state:
    st.session_state.user = None
if "materia_seleccionada_id" not in st.session_state:
    st.session_state.materia_seleccionada_id = None
if "examen_en_curso" not in st.session_state:
    st.session_state.examen_en_curso = None
if "tiempo_inicio_examen" not in st.session_state:
    st.session_state.tiempo_inicio_examen = None

def login(usuario, clave):
    res = c.execute("SELECT id, username, nombre, email, rol FROM usuarios WHERE username = ? AND password = ?", (usuario, clave)).fetchone()
    if res:
        st.session_state.user = {"id": res[0], "username": res[1], "nombre": res[2], "email": res[3], "rol": res[4]}
        return True
    return False

def logout():
    st.session_state.user = None
    st.session_state.materia_seleccionada_id = None
    st.session_state.examen_en_curso = None
    st.session_state.tiempo_inicio_examen = None
    st.rerun()

# --- PANTALLA DE ACCESO / LOGIN ---
if st.session_state.user is None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='brand-title' style='text-align: center;'>🎓 Plataforma Educativa</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><span class='brand-badge'>Created by Tec. Cristian Nuñez</span></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("form_login"):
            st.subheader("Ingreso al Campus Virtual")
            u_input = st.text_input("Usuario")
            p_input = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Acceder al Sistema", use_container_width=True):
                if login(u_input, p_input):
                    st.success("Acceso concedido.")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas (Profesor inicial: `profesor`/`1234`)")
    st.stop()

# --- ENCABEZADO GLOBAL ---
u = st.session_state.user
col_h1, col_h2, col_h3 = st.columns([3, 5, 4])
with col_h1:
    if st.button("🏛️ Área personal", key="btn_home"):
        st.session_state.materia_seleccionada_id = None
        st.rerun()

with col_h2:
    st.markdown(f"**🎓 Plataforma Educativa** &nbsp;|&nbsp; {u['nombre']} (`{u['rol'].capitalize()}`)<br><small style='color: #0369a1;'>Created by Tec. Cristian Nuñez</small>", unsafe_allow_html=True)

with col_h3:
    c_btn1, c_btn2 = st.columns([1, 1])
    with c_btn1:
        with st.popover("🔑 Cambiar Clave"):
            with st.form("form_cambio_clave_usuario"):
                st.markdown("##### Actualizar Contraseña")
                pass_act = st.text_input("Contraseña actual", type="password")
                pass_n1 = st.text_input("Nueva contraseña", type="password")
                pass_n2 = st.text_input("Confirmar nueva contraseña", type="password")
                if st.form_submit_button("Guardar Cambios"):
                    chk = c.execute("SELECT id FROM usuarios WHERE id = ? AND password = ?", (u["id"], pass_act)).fetchone()
                    if not chk:
                        st.error("La contraseña actual es incorrecta.")
                    elif pass_n1 != pass_n2:
                        st.error("Las nuevas contraseñas no coinciden.")
                    elif len(pass_n1) < 3:
                        st.error("La contraseña debe tener al menos 3 caracteres.")
                    else:
                        c.execute("UPDATE usuarios SET password = ? WHERE id = ?", (pass_n1, u["id"]))
                        conn.commit()
                        st.success("¡Contraseña actualizada con éxito!")
    with c_btn2:
        if st.button("Cerrar sesión", key="btn_logout_top"):
            logout()

st.divider()

# ==============================================================================
# 👨‍🏫 VISTA PROFESOR / DOCENTE
# ==============================================================================
if u["rol"] == "profesor":

    st.sidebar.markdown("### 🏛️ Administración Docente")
    
    # Configuración de Servidor de Correo
    with st.sidebar.expander("📧 Configurar Notificaciones por Email"):
        with st.form("form_smtp_cfg"):
            smtp_mail_act = get_config("smtp_email", "")
            smtp_pass_act = get_config("smtp_password", "")
            n_mail = st.text_input("Tu Gmail emisor", value=smtp_mail_act)
            n_pass = st.text_input("Contraseña de Aplicación (16 letras)", value=smtp_pass_act, type="password", help="Generala en tu Cuenta Google > Seguridad > Contraseñas de aplicaciones.")
            if st.form_submit_button("Guardar Configuración"):
                set_config("smtp_email", n_mail.strip())
                set_config("smtp_password", n_pass.strip())
                st.success("Configuración guardada.")

    # Crear Nuevo Docente
    with st.sidebar.expander("👨‍🏫 Crear Nuevo Usuario Profesor"):
        with st.form("form_crear_nuevo_profe", clear_on_submit=True):
            nom_p = st.text_input("Nombre y Apellido del Profesor")
            mail_p = st.text_input("Email Docente")
            usr_p = st.text_input("Usuario Docente")
            pwd_p = st.text_input("Contraseña", value="1234")
            if st.form_submit_button("Registrar Profesor"):
                if nom_p and mail_p and usr_p and pwd_p:
                    try:
                        c.execute("INSERT INTO usuarios (username, password, nombre, email, rol) VALUES (?, ?, ?, ?, 'profesor')",
                                  (usr_p, pwd_p, nom_p, mail_p))
                        conn.commit()
                        st.success(f"Profesor {nom_p} registrado con éxito.")
                    except sqlite3.IntegrityError:
                        st.error("El nombre de usuario o email ya existe.")

    # DASHBOARD DE CURSOS
    if st.session_state.materia_seleccionada_id is None:
        st.markdown("## **Vista General de Cursos**")
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            with st.popover("➕ Crear Curso"):
                with st.form("form_crear_materia", clear_on_submit=True):
                    nom_mat = st.text_input("Nombre del Curso")
                    cod_mat = st.text_input("Código de Comisión (ej: LSO-4TO)")
                    cat_mat = st.text_input("Categoría", value="Categoría 1")
                    if st.form_submit_button("Guardar Curso") and nom_mat and cod_mat:
                        try:
                            c.execute("INSERT INTO catedras (nombre, codigo, categoria, profesor_id) VALUES (?, ?, ?, ?)",
                                      (nom_mat, cod_mat, cat_mat, u["id"]))
                            conn.commit()
                            st.success("Materia creada.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Ya existe una materia con ese código.")

        df_materias = pd.read_sql("SELECT id, nombre, codigo, categoria FROM catedras WHERE profesor_id = ?", conn, params=(u["id"],))

        if df_materias.empty:
            st.info("Aún no tienes cursos creados. Pulsa '➕ Crear Curso' para comenzar.")
        else:
            cols = st.columns(3)
            banners = ["card-banner-1", "card-banner-2", "card-banner-3", "card-banner-4"]
            for idx, row in df_materias.iterrows():
                banner = banners[idx % len(banners)]
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class='course-card'>
                        <div class='{banner}'></div>
                        <div class='course-card-body'>
                            <div class='course-title'>{row['nombre']}</div>
                            <div class='course-cat'>{row['categoria']} • {row['codigo']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Entrar al curso ➜", key=f"entrar_{row['id']}"):
                        st.session_state.materia_seleccionada_id = row['id']
                        st.rerun()

    # DENTRO DE UNA MATERIA
    else:
        cat_id = st.session_state.materia_seleccionada_id
        res_cat = c.execute("SELECT nombre, codigo FROM catedras WHERE id = ?", (cat_id,)).fetchone()
        nombre_materia = res_cat[0]

        if st.sidebar.button("⬅️ Volver a mis Cursos"):
            st.session_state.materia_seleccionada_id = None
            st.rerun()

        st.markdown(f"## **{nombre_materia}**")

        tab_curso, tab_participantes, tab_calificaciones = st.tabs(["📘 Curso", "👥 Participantes", "📈 Calificaciones"])

        # --- 1. PESTAÑA CURSO (CON EDICIÓN DE UNIDADES) ---
        with tab_curso:
            col_sec1, col_sec2 = st.columns([3, 1])
            with col_sec2:
                with st.popover("➕ Añadir Nueva Sección / Tema"):
                    with st.form("form_nueva_secc", clear_on_submit=True):
                        nom_secc = st.text_input("Nombre de la Sección (ej: Unidad 1)")
                        if st.form_submit_button("Crear Sección") and nom_secc:
                            orden_max = c.execute("SELECT COALESCE(MAX(orden), 0) + 1 FROM secciones WHERE catedra_id = ?", (cat_id,)).fetchone()[0]
                            c.execute("INSERT INTO secciones (catedra_id, titulo, orden) VALUES (?, ?, ?)", (cat_id, nom_secc, orden_max))
                            conn.commit()
                            st.success("Sección creada.")
                            st.rerun()

            with st.expander("➕ Añadir una actividad o un recurso"):
                df_secc = pd.read_sql("SELECT id, titulo FROM secciones WHERE catedra_id = ? ORDER BY orden ASC", conn, params=(cat_id,))
                if df_secc.empty:
                    st.warning("Primero creá al menos una sección arriba para añadir actividades.")
                else:
                    tipo_modulo = st.selectbox("Tipo de recurso:", ["📝 Tarea (Entrega de Archivo/Texto)", "⏱️ Cuestionario / Examen por Tiempo", "📁 Archivo / URL"])
                    sec_map = {r['titulo']: r['id'] for _, r in df_secc.iterrows()}
                    sec_elegida = st.selectbox("Sección de destino:", list(sec_map.keys()))

                    with st.form("form_alta_actividad", clear_on_submit=True):
                        tit_act = st.text_input("Título de la actividad")
                        desc_act = st.text_area("Descripción / Consigna")
                        dur_min = 0
                        json_preguntas = None
                        if "Examen" in tipo_modulo:
                            dur_min = st.number_input("Duración del examen (minutos):", min_value=1, max_value=180, value=10)
                            st.markdown("**Configurar 2 preguntas de prueba:**")
                            p1_txt = st.text_input("Pregunta 1:", value="¿Qué capa del modelo OSI maneja el direccionamiento IP?")
                            p1_op = st.text_input("Opciones P1 (separadas por coma):", value="Capa de Transporte, Capa de Red, Capa de Enlace")
                            p1_cor = st.text_input("Opción Correcta P1:", value="Capa de Red")

                            p2_txt = st.text_input("Pregunta 2:", value="¿Cuál es el protocolo utilizado para navegación web segura?")
                            p2_op = st.text_input("Opciones P2 (separadas por coma):", value="HTTP, FTP, HTTPS")
                            p2_cor = st.text_input("Opción Correcta P2:", value="HTTPS")

                            json_preguntas = json.dumps([
                                {"pregunta": p1_txt, "opciones": [x.strip() for x in p1_op.split(",")], "correcta": p1_cor.strip()},
                                {"pregunta": p2_txt, "opciones": [x.strip() for x in p2_op.split(",")], "correcta": p2_cor.strip()}
                            ])

                        f_lim = st.date_input("Fecha Límite", min_value=date.today())
                        enlace_url = st.text_input("Enlace web / URL (si corresponde)")

                        if st.form_submit_button("Guardar y mostrar en el curso") and tit_act:
                            tipo_db = "Cuestionario" if "Examen" in tipo_modulo else ("Tarea" if "Tarea" in tipo_modulo else "Archivo")
                            c.execute("""
                                INSERT INTO actividades (catedra_id, seccion_id, titulo, tipo, fecha_limite, duracion_minutos, preguntas_json, descripcion, enlace_archivo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (cat_id, sec_map[sec_elegida], tit_act, tipo_db, str(f_lim), dur_min, json_preguntas, desc_act, enlace_url))
                            conn.commit()
                            st.success("Actividad publicada.")
                            st.rerun()

            # Renderizado de Secciones con botones de EDITAR y BORRAR
            df_secciones = pd.read_sql("SELECT id, titulo FROM secciones WHERE catedra_id = ? ORDER BY orden ASC", conn, params=(cat_id,))
            if df_secciones.empty:
                st.info("No hay secciones creadas en este curso. Usa el botón '➕ Añadir Nueva Sección / Tema' arriba.")
            else:
                for _, sec in df_secciones.iterrows():
                    col_s_tit, col_s_edit, col_s_del = st.columns([5, 1, 1])
                    with col_s_tit:
                        st.markdown(f"#### 📂 {sec['titulo']}")
                    
                    with col_s_edit:
                        with st.popover("✏️ Editar", key=f"pop_edit_{sec['id']}"):
                            with st.form(f"form_renombrar_{sec['id']}"):
                                nuevo_nombre = st.text_input("Nuevo nombre:", value=sec['titulo'])
                                if st.form_submit_button("Guardar") and nuevo_nombre:
                                    c.execute("UPDATE secciones SET titulo = ? WHERE id = ?", (nuevo_nombre.strip(), sec['id']))
                                    conn.commit()
                                    st.success("Sección actualizada.")
                                    st.rerun()

                    with col_s_del:
                        if st.button("🗑️ Borrar", key=f"del_sec_{sec['id']}"):
                            c.execute("DELETE FROM actividades WHERE seccion_id = ?", (sec['id'],))
                            c.execute("DELETE FROM secciones WHERE id = ?", (sec['id'],))
                            conn.commit()
                            st.rerun()

                    acts = pd.read_sql("SELECT * FROM actividades WHERE seccion_id = ?", conn, params=(sec['id'],))
                    if acts.empty:
                        st.caption("No hay contenidos cargados en esta sección.")
                    else:
                        for _, a in acts.iterrows():
                            ico = "⏱️" if a['tipo'] == 'Cuestionario' else ("📄" if a['tipo'] == 'Tarea' else "🔗")
                            t_lbl = f" | ⏳ {a['duracion_minutos']} min" if a['duracion_minutos'] > 0 else ""
                            st.markdown(f"> {ico} **{a['titulo']}** ({a['tipo']}){t_lbl} — *Vence: {a['fecha_limite']}*")

        # --- 2. PESTAÑA PARTICIPANTES (CON ENVÍO DE EMAIL AL REGISTRAR) ---
        with tab_participantes:
            st.markdown("### **Matriculación de Alumnos**")
            col_m1, col_m2 = st.columns([1, 1])
            with col_m1:
                with st.expander("➕ Dar de alta nuevo alumno con Mail Personal", expanded=True):
                    with st.form("form_alta_alumno_mail", clear_on_submit=True):
                        nom_a = st.text_input("Nombre y Apellido Completo")
                        mail_a = st.text_input("Email Personal del Alumno")
                        usr_a = st.text_input("Usuario Asignado")
                        pwd_a = st.text_input("Contraseña Asignada", value="1234")
                        
                        if st.form_submit_button("Registrar, Matricular y Notificar por Mail"):
                            if nom_a and mail_a and usr_a and pwd_a:
                                try:
                                    c.execute("INSERT INTO usuarios (username, password, nombre, email, rol) VALUES (?, ?, ?, ?, 'estudiante')",
                                              (usr_a, pwd_a, nom_a, mail_a))
                                    nuevo_u_id = c.lastrowid
                                    c.execute("INSERT INTO matriculas (catedra_id, estudiante_id) VALUES (?, ?)", (cat_id, nuevo_u_id))
                                    conn.commit()

                                    # Enviar email automático
                                    ok_mail, msg_mail = enviar_credenciales_alumno(mail_a.strip(), nom_a, nombre_materia, usr_a, pwd_a)
                                    if ok_mail:
                                        st.success(f"Alumno {nom_a} matriculado y credenciales enviadas a {mail_a}.")
                                    else:
                                        st.warning(f"Alumno registrado y matriculado. Nota del correo: {msg_mail}")
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("El usuario o email ya existe en el sistema.")

            with col_m2:
                with st.expander("🔍 Matricular alumno ya existente"):
                    alumnos_db = pd.read_sql("SELECT id, nombre, email, username FROM usuarios WHERE rol = 'estudiante'", conn)
                    if not alumnos_db.empty:
                        map_existentes = {f"{r['nombre']} ({r['email']})": r['id'] for _, r in alumnos_db.iterrows()}
                        sel_ex = st.selectbox("Seleccionar estudiante:", list(map_existentes.keys()))
                        if st.button("Matricular alumno"):
                            try:
                                c.execute("INSERT INTO matriculas (catedra_id, estudiante_id) VALUES (?, ?)", (cat_id, map_existentes[sel_ex]))
                                conn.commit()
                                st.success("Matriculado correctamente.")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.warning("Ya se encuentra matriculado en esta materia.")

            st.markdown("### **Lista de Matriculados**")
            df_matriculados = pd.read_sql("""
                SELECT u.nombre as 'Nombre / Apellido(s)', u.email as 'Dirección de correo', u.username as 'Usuario'
                FROM matriculas m
                JOIN usuarios u ON m.estudiante_id = u.id
                WHERE m.catedra_id = ?
                ORDER BY u.nombre ASC
            """, conn, params=(cat_id,))
            st.dataframe(df_matriculados, use_container_width=True, hide_index=True)

        # --- 3. PESTAÑA CALIFICACIONES ---
        with tab_calificaciones:
            st.markdown("### **Libro Central de Calificaciones**")
            
            alumnos_curso = pd.read_sql("""
                SELECT u.id, u.nombre, u.email 
                FROM matriculas m JOIN usuarios u ON m.estudiante_id = u.id 
                WHERE m.catedra_id = ? ORDER BY u.nombre ASC
            """, conn, params=(cat_id,))

            acts_curso = pd.read_sql("SELECT id, titulo FROM actividades WHERE catedra_id = ? AND tipo IN ('Tarea', 'Cuestionario')", conn, params=(cat_id,))

            if alumnos_curso.empty:
                st.info("No hay alumnos matriculados en esta cátedra.")
            elif acts_curso.empty:
                st.info("No hay actividades evaluativas creadas.")
            else:
                tabla_calif = []
                for _, al in alumnos_curso.iterrows():
                    iniciales = "".join([part[0] for part in al['nombre'].split()[:2]]).upper()
                    fila = {
                        "Avatar": iniciales,
                        "Nombre / Apellido(s)": al['nombre'],
                        "Dirección de correo": al['email']
                    }
                    total_notas = []
                    for _, act in acts_curso.iterrows():
                        res_nota = c.execute("SELECT nota FROM entregas WHERE actividad_id = ? AND estudiante_id = ?", (act['id'], al['id'])).fetchone()
                        if res_nota and res_nota[0] is not None:
                            fila[act['titulo']] = f"{res_nota[0]:.2f}"
                            total_notas.append(res_nota[0])
                        else:
                            fila[act['titulo']] = "-"
                    
                    fila["Promedio"] = f"{(sum(total_notas)/len(total_notas)):.2f}" if total_notas else "-"
                    tabla_calif.append(fila)

                df_render = pd.DataFrame(tabla_calif)
                
                prom_cols = {"Avatar": "∑", "Nombre / Apellido(s)": "Promedio general", "Dirección de correo": ""}
                for _, act in acts_curso.iterrows():
                    todas_notas = [float(x[act['titulo']]) for x in tabla_calif if x[act['titulo']] != "-"]
                    prom_cols[act['titulo']] = f"{(sum(todas_notas)/len(todas_notas)):.2f}" if todas_notas else "-"
                
                todas_prom = [float(x["Promedio"]) for x in tabla_calif if x["Promedio"] != "-"]
                prom_cols["Promedio"] = f"{(sum(todas_prom)/len(todas_prom)):.2f}" if todas_prom else "-"
                
                df_render = pd.concat([df_render, pd.DataFrame([prom_cols])], ignore_index=True)
                st.dataframe(df_render, use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("### **Revisión Detallada de Exámenes y Devoluciones**")
            
            entregas_db = pd.read_sql("""
                SELECT e.id as entrega_id, u.nombre as alumno, u.email, a.titulo as examen, a.tipo as tipo_actividad, a.preguntas_json,
                       e.respuesta_data, e.archivo_ruta, e.nota, e.devolucion, e.tiempo_empleado_seg, e.fecha_entrega
                FROM entregas e
                JOIN actividades a ON e.actividad_id = a.id
                JOIN usuarios u ON e.estudiante_id = u.id
                WHERE a.catedra_id = ?
            """, conn, params=(cat_id,))

            if not entregas_db.empty:
                for _, ent in entregas_db.iterrows():
                    t_min = f" | ⏱️ Tiempo empleado: {round(ent['tiempo_empleado_seg']/60, 1)} min" if ent['tiempo_empleado_seg'] else ""
                    with st.expander(f"📌 {ent['alumno']} - {ent['examen']} ({ent['tipo_actividad']}) | Nota: {ent['nota']}{t_min}"):
                        st.caption(f"📅 **Fecha de Entrega:** {ent['fecha_entrega']}")
                        
                        # Si es Examen / Cuestionario
                        if ent['preguntas_json'] and ent['respuesta_data']:
                            st.markdown("#### **Desglose de Preguntas:**")
                            try:
                                preguntas = json.loads(ent['preguntas_json'])
                                rtas_al = json.loads(ent['respuesta_data'])
                                for idx, preg in enumerate(preguntas):
                                    rta_dada = rtas_al.get(str(idx), "Sin responder")
                                    es_correcta = (rta_dada == preg['correcta'])
                                    
                                    if es_correcta:
                                        st.markdown(f"""
                                        <div class='q-correct'>
                                            <b>Pregunta {idx+1}:</b> {preg['pregunta']}<br>
                                            ✅ <b>Respuesta del alumno:</b> {rta_dada} (Correcta)
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"""
                                        <div class='q-wrong'>
                                            <b>Pregunta {idx+1}:</b> {preg['pregunta']}<br>
                                            ❌ <b>Respuesta del alumno:</b> {rta_dada}<br>
                                            ✔️ <b>Opción Correcta:</b> {preg['correcta']}
                                        </div>
                                        """, unsafe_allow_html=True)
                            except Exception:
                                st.write(f"Respuestas: {ent['respuesta_data']}")

                        # Si es Tarea (Texto o Archivo Adjunto)
                        else:
                            st.markdown("#### **Contenido Entregado por el Alumno:**")
                            if ent['respuesta_data']:
                                st.markdown(f"""
                                <div class='task-response-box'>
                                    <b>📝 Texto / Desarrollo enviado:</b><br>
                                    {ent['respuesta_data']}
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.write("*(Sin texto desarrollado)*")

                            # Botón de Descarga del Archivo Adjunto
                            if ent['archivo_ruta'] and os.path.exists(ent['archivo_ruta']):
                                nombre_archivo_real = os.path.basename(ent['archivo_ruta'])
                                with open(ent['archivo_ruta'], "rb") as f_adj:
                                    st.download_button(
                                        label=f"📥 Descargar Archivo Adjunto ({nombre_archivo_real})",
                                        data=f_adj.read(),
                                        file_name=nombre_archivo_real,
                                        key=f"dl_{ent['entrega_id']}"
                                    )
                            elif ent['archivo_ruta']:
                                st.warning(f"Archivo registrado: `{os.path.basename(ent['archivo_ruta'])}` (no encontrado en almacenamiento temporal).")
                            else:
                                st.info("El alumno no adjuntó archivos en esta entrega.")

                        # Formulario para Calificar y Devolver
                        with st.form(f"form_corr_{ent['entrega_id']}"):
                            n_nueva = st.number_input("Calificación Final", min_value=0.0, max_value=10.0, value=float(ent['nota']) if ent['nota'] is not None else 7.0)
                            dev_nueva = st.text_area("Devolución Pedagógica para el Alumno", value=ent['devolucion'] if ent['devolucion'] else "")
                            if st.form_submit_button("Guardar Calificación y Devolución"):
                                c.execute("UPDATE entregas SET nota = ?, devolucion = ? WHERE id = ?", (n_nueva, dev_nueva, ent['entrega_id']))
                                conn.commit()
                                st.success("Calificación guardada exitosamente.")
                                st.rerun()
            else:
                st.info("No hay exámenes o tareas entregadas pendientes de revisión.")

# ==============================================================================
# 🎓 VISTA ESTUDIANTE
# ==============================================================================
else:
    st.markdown("## **Mis Cursos**")
    
    df_mis_cursos = pd.read_sql("""
        SELECT c.id, c.nombre, c.codigo, c.categoria 
        FROM catedras c JOIN matriculas m ON c.id = m.catedra_id 
        WHERE m.estudiante_id = ?
    """, conn, params=(u["id"],))

    if df_mis_cursos.empty:
        st.warning("No estás matriculado en ninguna materia aún.")
        st.stop()

    mat_map = {f"{r['nombre']} ({r['codigo']})": r['id'] for _, r in df_mis_cursos.iterrows()}
    sel_mat_al = st.selectbox("Seleccionar Curso:", list(mat_map.keys()))
    materia_id = mat_map[sel_mat_al]

    tab_al_curso, tab_al_notas = st.tabs(["📘 Curso y Evaluaciones", "📊 Mis Calificaciones"])

    with tab_al_curso:
        df_sec_al = pd.read_sql("SELECT id, titulo FROM secciones WHERE catedra_id = ? ORDER BY orden ASC", conn, params=(materia_id,))
        for _, s in df_sec_al.iterrows():
            st.markdown(f"#### 📂 {s['titulo']}")
            acts_al = pd.read_sql("SELECT * FROM actividades WHERE seccion_id = ?", conn, params=(s['id'],))
            
            for _, act in acts_al.iterrows():
                ent_al = pd.read_sql("SELECT * FROM entregas WHERE actividad_id = ? AND estudiante_id = ?", conn, params=(act['id'], u['id']))
                ya_rendido = not ent_al.empty
                
                with st.expander(f"📌 {act['titulo']} ({act['tipo']}) | {'✅ Completado' if ya_rendido else '⏳ Pendiente'}"):
                    st.write(f"**Consigna:** {act['descripcion']}")
                    
                    if ya_rendido:
                        data_ent = ent_al.iloc[0]
                        st.success(f"Entregado el: {data_ent['fecha_entrega']}")
                        if data_ent['nota'] is not None:
                            st.metric("Calificación:", f"{data_ent['nota']}/10")
                            st.info(f"**Devolución del Profesor:**\n{data_ent['devolucion']}")
                    else:
                        if act['tipo'] == "Cuestionario":
                            st.warning(f"⏱️ Este examen tiene un tiempo límite de **{act['duracion_minutos']} minutos**.")
                            
                            if st.session_state.examen_en_curso != act['id']:
                                if st.button("🚀 Comenzar Examen Ahora", key=f"start_{act['id']}"):
                                    st.session_state.examen_en_curso = act['id']
                                    st.session_state.tiempo_inicio_examen = time.time()
                                    st.rerun()

                            if st.session_state.examen_en_curso == act['id']:
                                t_pasado = int(time.time() - st.session_state.tiempo_inicio_examen)
                                t_total = act['duracion_minutos'] * 60
                                t_restante = max(0, t_total - t_pasado)
                                
                                mins, segs = divmod(t_restante, 60)
                                st.markdown(f"<div class='timer-box'>⏳ Tiempo Restante: {mins:02d}:{segs:02d}</div>", unsafe_allow_html=True)
                                
                                pregs = json.loads(act['preguntas_json']) if act['preguntas_json'] else []
                                rtas_seleccionadas = {}
                                
                                with st.form(f"form_rendir_{act['id']}"):
                                    for idx, p in enumerate(pregs):
                                        st.markdown(f"**Pregunta {idx+1}:** {p['pregunta']}")
                                        rtas_seleccionadas[idx] = st.radio("Opción:", p['opciones'], key=f"ans_{act['id']}_{idx}")
                                    
                                    if st.form_submit_button("Terminar y Enviar Examen") or t_restante == 0:
                                        aciertos = sum(1 for idx, p in enumerate(pregs) if rtas_seleccionadas.get(idx) == p['correcta'])
                                        nota_calc = round((aciertos / len(pregs)) * 10, 2) if pregs else 10.0
                                        dev_auto = f"Autocorrección del sistema: {aciertos} de {len(pregs)} respuestas correctas."
                                        
                                        c.execute("""
                                            INSERT INTO entregas (actividad_id, estudiante_id, fecha_entrega, respuesta_data, nota, devolucion, tiempo_empleado_seg)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """, (act['id'], u['id'], datetime.now().strftime("%Y-%m-%d %H:%M"), json.dumps(rtas_seleccionadas), nota_calc, dev_auto, t_pasado))
                                        conn.commit()
                                        st.session_state.examen_en_curso = None
                                        st.session_state.tiempo_inicio_examen = None
                                        st.success(f"Examen finalizado. Nota: {nota_calc}/10")
                                        st.rerun()
                        else:
                            with st.form(f"form_tarea_{act['id']}"):
                                rta_t = st.text_area("Desarrollo de la entrega (texto / informe)")
                                arch = st.file_uploader("Adjuntar archivo (PDF, Word, etc.)", type=["pdf", "docx", "zip", "txt", "xlsx", "pptx"])
                                if st.form_submit_button("Enviar Tarea"):
                                    r_path = None
                                    if arch is not None:
                                        r_path = os.path.join(CARPETA_ENTREGAS, f"{u['id']}_{act['id']}_{arch.name}")
                                        with open(r_path, "wb") as f:
                                            f.write(arch.getbuffer())
                                    c.execute("INSERT INTO entregas (actividad_id, estudiante_id, fecha_entrega, respuesta_data, archivo_ruta) VALUES (?, ?, ?, ?, ?)",
                                              (act['id'], u['id'], datetime.now().strftime("%Y-%m-%d %H:%M"), rta_t, r_path))
                                    conn.commit()
                                    st.success("Tarea enviada correctamente.")
                                    st.rerun()

    with tab_al_notas:
        st.markdown("### **Mis Calificaciones**")
        df_notas_al = pd.read_sql("""
            SELECT a.titulo as Actividad, a.tipo as Tipo, e.nota as Calificación, e.devolucion as Devolución, e.fecha_entrega as 'Fecha de Entrega'
            FROM actividades a
            LEFT JOIN entregas e ON a.id = e.actividad_id AND e.estudiante_id = ?
            WHERE a.catedra_id = ?
        """, conn, params=(u['id'], materia_id))
        st.dataframe(df_notas_al, use_container_width=True, hide_index=True)
