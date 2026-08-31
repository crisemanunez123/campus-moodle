import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import time
import re
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
    .drag-word-box { background: #e0f2fe; border: 1px solid #0284c7; padding: 4px 10px; border-radius: 4px; font-weight: bold; color: #0369a1; display: inline-block; margin: 2px; }
    .forum-msg-docente {
        background-color: #e0f2fe;
        border-left: 5px solid #0284c7;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .forum-msg-alumno {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #64748b;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS LOCAL Y AUTO-MIGRACIÓN ---
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

try:
    cols_usuarios = [col[1] for col in c.execute("PRAGMA table_info(usuarios)").fetchall()]
    if "email" not in cols_usuarios:
        c.execute("ALTER TABLE usuarios ADD COLUMN email TEXT")
    if "rol" not in cols_usuarios:
        c.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT")
    conn.commit()
except Exception:
    pass

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
CREATE TABLE IF NOT EXISTS asistencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catedra_id INTEGER,
    estudiante_id INTEGER,
    fecha TEXT,
    estado TEXT,
    UNIQUE(catedra_id, estudiante_id, fecha),
    FOREIGN KEY(catedra_id) REFERENCES catedras(id),
    FOREIGN KEY(estudiante_id) REFERENCES usuarios(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS foro_mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actividad_id INTEGER,
    usuario_id INTEGER,
    mensaje TEXT,
    fecha TEXT,
    FOREIGN KEY(actividad_id) REFERENCES actividades(id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT
)
""")
conn.commit()

# --- FUNCIONES DE UTILIDAD ---
def get_config(clave, default=""):
    r = c.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
    return r[0] if r else default

def set_config(clave, valor):
    c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", (clave, valor))
    conn.commit()

def es_enlace_video(url):
    if not url:
        return False
    patrones_video = [
        r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/",
        r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/",
        r"\.(?:mp4|webm|ogg|mov)$"
    ]
    return any(re.search(patron, url.strip(), re.IGNORECASE) for patron in patrones_video)

def renderizar_recurso_multimedia(enlace):
    if not enlace:
        return
    enlace_limpio = enlace.strip()
    if es_enlace_video(enlace_limpio):
        st.markdown("🎬 **Reproductor de Video:**")
        try:
            st.video(enlace_limpio)
        except Exception:
            st.markdown(f"🔗 **Enlace del video:** [{enlace_limpio}]({enlace_limpio})")
    else:
        st.markdown(f"🔗 **Enlace adjunto:** [{enlace_limpio}]({enlace_limpio})")

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
    res = c.execute("SELECT id, username, nombre, email, rol, password FROM usuarios WHERE username = ? AND password = ?", (usuario, clave)).fetchone()
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
    
    with st.sidebar.expander("📧 Configurar Notificaciones por Email"):
        with st.form("form_smtp_cfg"):
            smtp_mail_act = get_config("smtp_email", "")
            smtp_pass_act = get_config("smtp_password", "")
            n_mail = st.text_input("Tu Gmail emisor", value=smtp_mail_act)
            n_pass = st.text_input("Contraseña de Aplicación (16 letras)", value=smtp_pass_act, type="password")
            if st.form_submit_button("Guardar Configuración"):
                set_config("smtp_email", n_mail.strip())
                set_config("smtp_password", n_pass.strip())
                st.success("Configuración guardada.")

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
                                  (usr_p.strip(), pwd_p.strip(), nom_p.strip(), mail_p.strip()))
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

        st.subheader(f"🏛️ {nombre_materia}")

        tab_curso, tab_participantes, tab_calificaciones, tab_asistencia = st.tabs(["📘 Curso", "👥 Participantes", "📈 Calificaciones", "📋 Asistencia"])

        # --- 1. PESTAÑA CURSO ---
        with tab_curso:
            col_sec1, col_sec2 = st.columns([3, 1])
            with col_sec2:
                with st.popover("➕ Añadir Nueva Sección / Unidad"):
                    with st.form("form_nueva_secc", clear_on_submit=True):
                        nom_secc = st.text_input("Nombre de la Sección (ej: Unidad 1)")
                        if st.form_submit_button("Crear Sección") and nom_secc:
                            orden_max = c.execute("SELECT COALESCE(MAX(orden), 0) + 1 FROM secciones WHERE catedra_id = ?", (cat_id,)).fetchone()[0]
                            c.execute("INSERT INTO secciones (catedra_id, titulo, orden) VALUES (?, ?, ?)", (cat_id, nom_secc.strip(), orden_max))
                            conn.commit()
                            st.success("Sección creada.")
                            st.rerun()

            with st.expander("➕ Añadir una actividad o un recurso"):
                df_secc = pd.read_sql("SELECT id, titulo FROM secciones WHERE catedra_id = ? ORDER BY orden ASC", conn, params=(cat_id,))
                if df_secc.empty:
                    st.warning("Primero creá al menos una sección arriba para añadir actividades.")
                else:
                    tipo_modulo = st.selectbox("Tipo de recurso:", [
                        "💬 Foro (Debate e Interacción)",
                        "⏱️ Cuestionario / Examen Dinámico por Tiempo",
                        "📝 Tarea (Entrega de Archivo/Texto)",
                        "📁 Archivo / URL / Video"
                    ])
                    sec_map = {r['titulo']: r['id'] for _, r in df_secc.iterrows()}
                    sec_elegida = st.selectbox("Sección de destino:", list(sec_map.keys()))

                    tit_act = st.text_input("Título de la actividad / foro / examen / video", placeholder="Ej: Video Clase Magistral / Examen Parcial")
                    desc_act = st.text_area("Descripción / Consigna general", placeholder="Instrucciones para los participantes...")
                    f_lim = st.date_input("Fecha Límite", min_value=date.today())

                    dur_min = 0
                    preguntas_generadas = []

                    if "Examen" in tipo_modulo:
                        st.markdown("---")
                        st.markdown("### 🛠️ **Configuración del Examen por Tiempo**")
                        dur_min = st.number_input("⏱️ Tiempo límite para responder (en minutos):", min_value=1, max_value=240, value=15)
                        
                        cant_pregs = st.number_input("Cantidad de preguntas / ítems a configurar:", min_value=1, max_value=25, value=2)
                        
                        for i in range(int(cant_pregs)):
                            num_preg = i + 1
                            st.markdown(f"#### **Pregunta N° {num_preg}**")
                            tipo_p = st.selectbox(f"Tipo de Pregunta N° {num_preg}:", 
                                                ["Opción Múltiple", "Verdadero o Falso", "Completar Párrafo (Palabras arrastrables)"], 
                                                key=f"tipo_p_{i}")
                            
                            if tipo_p == "Opción Múltiple":
                                enun = st.text_input(f"Enunciado de la Pregunta N° {num_preg}:", placeholder="Ej: ¿Qué órgano ejerce el poder judicial?", key=f"enun_mc_{i}")
                                cant_opciones = st.number_input(f"Cantidad de opciones para la Pregunta N° {num_preg}:", min_value=2, max_value=10, value=4, key=f"cant_ops_{i}")
                                
                                ops_cargadas = []
                                for op_idx in range(int(cant_opciones)):
                                    letra = chr(65 + op_idx)
                                    val_op = st.text_input(f"Opción {letra} (Pregunta N° {num_preg}):", key=f"op_{i}_{op_idx}")
                                    if val_op.strip():
                                        ops_cargadas.append(val_op.strip())
                                
                                if ops_cargadas:
                                    corr = st.selectbox(f"Seleccionar cuál es la Opción CORRECTA para la Pregunta N° {num_preg}:", ops_cargadas, key=f"corr_mc_sel_{i}")
                                    if enun.strip():
                                        preguntas_generadas.append({
                                            "tipo": "multiple_choice",
                                            "enunciado": enun.strip(),
                                            "opciones": ops_cargadas,
                                            "correcta": corr
                                        })
                            
                            elif tipo_p == "Verdadero o Falso":
                                enun_vf = st.text_input(f"Enunciado de la Pregunta N° {num_preg}:", placeholder="Ej: El artículo 14 bis garantiza los derechos del trabajador.", key=f"enun_vf_{i}")
                                corr_vf = st.radio(f"Respuesta correcta para la Pregunta N° {num_preg}:", ["Verdadero", "Falso"], horizontal=True, key=f"corr_vf_{i}")
                                if enun_vf.strip():
                                    preguntas_generadas.append({
                                        "tipo": "verdadero_falso",
                                        "enunciado": enun_vf.strip(),
                                        "opciones": ["Verdadero", "Falso"],
                                        "correcta": corr_vf
                                    })

                            elif tipo_p == "Completar Párrafo (Palabras arrastrables)":
                                st.info("💡 **Instrucciones:** Escribí el texto y encerrá entre corchetes `[palabra]` las palabras que el alumno deberá completar.\n*Ejemplo: El [Poder Judicial] es independiente del [Poder Ejecutivo].*")
                                texto_parrafo = st.text_area(f"Párrafo con lagunas [palabra] (Pregunta N° {num_preg}):", key=f"parr_{i}")
                                distractores = st.text_input(f"Palabras distractoras extras (opcional, separadas por coma):", placeholder="Legislativo, Ministro", key=f"distr_{i}")
                                
                                if texto_parrafo.strip():
                                    palabras_a_completar = re.findall(r'\[(.*?)\]', texto_parrafo)
                                    if palabras_a_completar:
                                        lista_distr = [x.strip() for x in distractores.split(",") if x.strip()]
                                        preguntas_generadas.append({
                                            "tipo": "completar_espacios",
                                            "enunciado": texto_parrafo.strip(),
                                            "palabras_correctas": palabras_a_completar,
                                            "distractores": lista_distr
                                        })

                    enlace_url = st.text_input("Enlace web / URL de Video (YouTube, Vimeo, MP4, etc.)", placeholder="https://www.youtube.com/watch?v=...")

                    if st.button("🚀 Publicar Actividad / Recurso en el Curso"):
                        if not tit_act.strip():
                            st.error("Por favor completá el título de la actividad.")
                        else:
                            if "Foro" in tipo_modulo:
                                tipo_db = "Foro"
                            elif "Examen" in tipo_modulo:
                                tipo_db = "Cuestionario"
                            elif "Tarea" in tipo_modulo:
                                tipo_db = "Tarea"
                            else:
                                tipo_db = "Archivo"

                            json_str = json.dumps(preguntas_generadas, ensure_ascii=False) if tipo_db == "Cuestionario" else None
                            
                            c.execute("""
                                INSERT INTO actividades (catedra_id, seccion_id, titulo, tipo, fecha_limite, duracion_minutos, preguntas_json, descripcion, enlace_archivo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (cat_id, sec_map[sec_elegida], tit_act.strip(), tipo_db, str(f_lim), dur_min, json_str, desc_act, enlace_url))
                            conn.commit()
                            st.success("¡Publicado exitosamente!")
                            st.rerun()

            # LISTA DE SECCIONES CON EDICIÓN COMPLETA
            df_secciones = pd.read_sql("SELECT id, titulo, orden FROM secciones WHERE catedra_id = ? ORDER BY orden ASC", conn, params=(cat_id,))
            if df_secciones.empty:
                st.info("No hay secciones creadas en este curso. Usa el botón '➕ Añadir Nueva Sección / Unidad' arriba.")
            else:
                for _, sec in df_secciones.iterrows():
                    st.divider()
                    col_s_tit, col_s_edit, col_s_del = st.columns([5, 1.2, 1])
                    with col_s_tit:
                        st.markdown(f"### 📂 **{sec['titulo']}**")
                    
                    with col_s_edit:
                        with st.popover("✏️ Modificar Sección", key=f"pop_edit_sec_{sec['id']}"):
                            with st.form(f"form_renombrar_{sec['id']}"):
                                st.markdown(f"##### Editar Sección #{sec['id']}")
                                nuevo_nombre = st.text_input("Título de la Sección", value=sec['titulo'])
                                nuevo_orden = st.number_input("Orden numérico", value=int(sec['orden']), min_value=1, step=1)
                                if st.form_submit_button("Guardar Modificaciones") and nuevo_nombre:
                                    c.execute("UPDATE secciones SET titulo = ?, orden = ? WHERE id = ?", (nuevo_nombre.strip(), nuevo_orden, sec['id']))
                                    conn.commit()
                                    st.success("Sección modificada.")
                                    st.rerun()

                    with col_s_del:
                        if st.button("🗑️ Borrar", key=f"del_sec_{sec['id']}"):
                            c.execute("DELETE FROM foro_mensajes WHERE actividad_id IN (SELECT id FROM actividades WHERE seccion_id = ?)", (sec['id'],))
                            c.execute("DELETE FROM entregas WHERE actividad_id IN (SELECT id FROM actividades WHERE seccion_id = ?)", (sec['id'],))
                            c.execute("DELETE FROM actividades WHERE seccion_id = ?", (sec['id'],))
                            c.execute("DELETE FROM secciones WHERE id = ?", (sec['id'],))
                            conn.commit()
                            st.rerun()

                    # ACTIVIDADES CON FORMATO PLEGABLE Y REPRODUCTOR DE VIDEO
                    acts = pd.read_sql("SELECT * FROM actividades WHERE seccion_id = ?", conn, params=(sec['id'],))
                    if acts.empty:
                        st.caption("No hay actividades cargadas en esta sección.")
                    else:
                        for _, a in acts.iterrows():
                            col_act_main, col_act_edit, col_act_del = st.columns([5, 1.2, 1])
                            
                            ico = "💬" if a['tipo'] == 'Foro' else ("⏱️" if a['tipo'] == 'Cuestionario' else ("📄" if a['tipo'] == 'Tarea' else ("🎬" if es_enlace_video(a['enlace_archivo']) else "🔗")))
                            t_lbl = f" | ⏳ {a['duracion_minutos']} min" if a['duracion_minutos'] > 0 else ""
                            
                            with col_act_main:
                                with st.expander(f"{ico} {a['titulo']} ({a['tipo']}){t_lbl} — Vence: {a['fecha_limite']}"):
                                    if a['descripcion']:
                                        st.markdown(f"**📌 Consigna / Descripción:**")
                                        st.markdown(a['descripcion'])
                                    else:
                                        st.caption("*(Sin descripción consignada)*")
                                    
                                    # Renderizador de video o enlace
                                    if a['enlace_archivo']:
                                        renderizar_recurso_multimedia(a['enlace_archivo'])

                                    # SI ES UN FORO: RENDERIZAR MENSAJES
                                    if a['tipo'] == 'Foro':
                                        st.divider()
                                        st.markdown("#### 💬 **Participaciones en el Foro:**")
                                        
                                        mensajes_foro = pd.read_sql("""
                                            SELECT m.id, m.mensaje, m.fecha, u.nombre, u.rol
                                            FROM foro_mensajes m
                                            JOIN usuarios u ON m.usuario_id = u.id
                                            WHERE m.actividad_id = ?
                                            ORDER BY m.id ASC
                                        """, conn, params=(a['id'],))

                                        if mensajes_foro.empty:
                                            st.info("Aún no hay mensajes en este foro. ¡Sé el primero en participar!")
                                        else:
                                            for _, m_row in mensajes_foro.iterrows():
                                                es_docente = (m_row['rol'] == 'profesor')
                                                clase_css = "forum-msg-docente" if es_docente else "forum-msg-alumno"
                                                badge_rol = "👨‍🏫 Docente" if es_docente else "🎓 Estudiante"
                                                
                                                st.markdown(f"""
                                                <div class='{clase_css}'>
                                                    <b>{m_row['nombre']}</b> &nbsp;<small style='color:#64748b;'>({badge_rol}) — {m_row['fecha']}</small><br>
                                                    <p style='margin-top: 6px; margin-bottom: 0px;'>{m_row['mensaje']}</p>
                                                </div>
                                                """, unsafe_allow_html=True)

                                        with st.form(f"form_responder_foro_profe_{a['id']}", clear_on_submit=True):
                                            txt_respuesta = st.text_area("Escribir aporte / intervención del docente en el foro:", key=f"txt_foro_p_{a['id']}")
                                            if st.form_submit_button("Publicar en el Foro") and txt_respuesta.strip():
                                                c.execute("""
                                                    INSERT INTO foro_mensajes (actividad_id, usuario_id, mensaje, fecha)
                                                    VALUES (?, ?, ?, ?)
                                                """, (a['id'], u['id'], txt_respuesta.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                                                conn.commit()
                                                st.success("Mensaje publicado.")
                                                st.rerun()

                            with col_act_edit:
                                with st.popover("✏️ Editar", key=f"pop_act_edit_{a['id']}"):
                                    with st.form(f"form_edit_act_{a['id']}"):
                                        st.markdown(f"##### Modificar Actividad: {a['titulo']}")
                                        n_tit_act = st.text_input("Título", value=a['titulo'])
                                        n_desc_act = st.text_area("Descripción / Consigna", value=a['descripcion'] if a['descripcion'] else "")
                                        
                                        try:
                                            fecha_actual = datetime.strptime(a['fecha_limite'], "%Y-%m-%d").date()
                                        except Exception:
                                            fecha_actual = date.today()
                                        n_f_lim = st.date_input("Fecha Límite", value=fecha_actual)
                                        
                                        n_dur = a['duracion_minutos']
                                        n_preg_json = a['preguntas_json']
                                        if a['tipo'] == "Cuestionario":
                                            n_dur = st.number_input("Duración (minutos):", min_value=1, max_value=240, value=int(a['duracion_minutos']))
                                            st.markdown("**Preguntas y Estructura del Examen (JSON):**")
                                            n_preg_json = st.text_area("Editar preguntas", value=a['preguntas_json'] if a['preguntas_json'] else "[]")

                                        n_enlace = st.text_input("Enlace URL / Video / Archivo", value=a['enlace_archivo'] if a['enlace_archivo'] else "")

                                        sec_opts = {r['titulo']: r['id'] for _, r in df_secciones.iterrows()}
                                        sec_actual_nom = [k for k, v in sec_opts.items() if v == a['seccion_id']]
                                        idx_default = list(sec_opts.keys()).index(sec_actual_nom[0]) if sec_actual_nom else 0
                                        n_sec_elegida = st.selectbox("Mover a sección:", list(sec_opts.keys()), index=idx_default)

                                        if st.form_submit_button("Guardar Cambios") and n_tit_act:
                                            c.execute("""
                                                UPDATE actividades 
                                                SET seccion_id = ?, titulo = ?, descripcion = ?, fecha_limite = ?, duracion_minutos = ?, preguntas_json = ?, enlace_archivo = ?
                                                WHERE id = ?
                                            """, (sec_opts[n_sec_elegida], n_tit_act.strip(), n_desc_act, str(n_f_lim), n_dur, n_preg_json, n_enlace, a['id']))
                                            conn.commit()
                                            st.success("Actividad modificada exitosamente.")
                                            st.rerun()

                            with col_act_del:
                                if st.button("🗑️", key=f"del_act_{a['id']}", help="Eliminar actividad"):
                                    c.execute("DELETE FROM foro_mensajes WHERE actividad_id = ?", (a['id'],))
                                    c.execute("DELETE FROM entregas WHERE actividad_id = ?", (a['id'],))
                                    c.execute("DELETE FROM actividades WHERE id = ?", (a['id'],))
                                    conn.commit()
                                    st.success("Actividad eliminada.")
                                    st.rerun()

        # --- 2. PESTAÑA PARTICIPANTES ---
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
                                              (usr_a.strip(), pwd_a.strip(), nom_a.strip(), mail_a.strip()))
                                    nuevo_u_id = c.lastrowid
                                    c.execute("INSERT INTO matriculas (catedra_id, estudiante_id) VALUES (?, ?)", (cat_id, nuevo_u_id))
                                    conn.commit()

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
                        
                        if ent['preguntas_json'] and ent['respuesta_data']:
                            st.markdown("#### **Desglose de Preguntas:**")
                            try:
                                preguntas = json.loads(ent['preguntas_json'])
                                rtas_al = json.loads(ent['respuesta_data'])
                                
                                for idx, preg in enumerate(preguntas):
                                    num_p = idx + 1
                                    t_p = preg.get("tipo", "multiple_choice")
                                    
                                    if t_p in ["multiple_choice", "verdadero_falso"]:
                                        rta_dada = rtas_al.get(str(idx), "Sin responder")
                                        es_correcta = (rta_dada == preg['correcta'])
                                        if es_correcta:
                                            st.markdown(f"""
                                            <div class='q-correct'>
                                                <b>Pregunta N° {num_p} ({t_p.replace('_',' ').capitalize()}):</b> {preg['enunciado']}<br>
                                                ✅ <b>Respuesta del alumno:</b> {rta_dada} (Correcta)
                                            </div>
                                            """, unsafe_allow_html=True)
                                        else:
                                            st.markdown(f"""
                                            <div class='q-wrong'>
                                                <b>Pregunta N° {num_p} ({t_p.replace('_',' ').capitalize()}):</b> {preg['enunciado']}<br>
                                                ❌ <b>Respuesta del alumno:</b> {rta_dada}<br>
                                                ✔️ <b>Opción Correcta:</b> {preg['correcta']}
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                    elif t_p == "completar_espacios":
                                        rtas_dadas = rtas_al.get(str(idx), {})
                                        correctas = preg['palabras_correctas']
                                        todas_bien = all(rtas_dadas.get(f"gap_{g_idx}") == cor for g_idx, cor in enumerate(correctas))
                                        
                                        texto_armado = preg['enunciado']
                                        for g_idx, cor in enumerate(correctas):
                                            val_al = rtas_dadas.get(f"gap_{g_idx}", "___")
                                            color_txt = "green" if val_al == cor else "red"
                                            texto_armado = texto_armado.replace(f"[{cor}]", f"<b style='color:{color_txt}'>[{val_al}]</b> (Correcto: {cor})")
                                        
                                        clase_box = "q-correct" if todas_bien else "q-wrong"
                                        st.markdown(f"""
                                        <div class='{clase_box}'>
                                            <b>Pregunta N° {num_p} (Completar Párrafo):</b><br>
                                            {texto_armado}
                                        </div>
                                        """, unsafe_allow_html=True)
                            except Exception:
                                st.write(f"Respuestas: {ent['respuesta_data']}")

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

        # --- 4. PESTAÑA ASISTENCIA ---
        with tab_asistencia:
            st.markdown("### **Control y Registro de Asistencia**")
            
            alumnos_asist = pd.read_sql("""
                SELECT u.id, u.nombre, u.email 
                FROM matriculas m JOIN usuarios u ON m.estudiante_id = u.id 
                WHERE m.catedra_id = ? ORDER BY u.nombre ASC
            """, conn, params=(cat_id,))

            if alumnos_asist.empty:
                st.info("No hay alumnos matriculados en esta materia para registrar asistencia.")
            else:
                col_f1, col_f2 = st.columns([2, 4])
                with col_f1:
                    fecha_sel = st.date_input("📅 Seleccionar Fecha de Clase:", value=date.today(), key="asist_fecha_sel")
                    fecha_str = str(fecha_sel)

                st.markdown(f"#### 📝 Tomar Asistencia para el día: **{fecha_str}**")

                with st.form(f"form_tomar_asistencia_{fecha_str}"):
                    estados_form = {}
                    cols_asist = st.columns([3, 2, 2])
                    cols_asist[0].markdown("**Alumno**")
                    cols_asist[1].markdown("**Email**")
                    cols_asist[2].markdown("**Estado**")

                    for _, al in alumnos_asist.iterrows():
                        reg_previo = c.execute("SELECT estado FROM asistencias WHERE catedra_id = ? AND estudiante_id = ? AND fecha = ?", (cat_id, al['id'], fecha_str)).fetchone()
                        val_defecto = reg_previo[0] if reg_previo else "Presente"
                        
                        c_a, c_b, c_c = st.columns([3, 2, 2])
                        c_a.write(f"👤 {al['nombre']}")
                        c_b.caption(al['email'])
                        estados_form[al['id']] = c_c.radio(
                            "Estado",
                            options=["Presente", "Ausente"],
                            index=0 if val_defecto == "Presente" else 1,
                            horizontal=True,
                            key=f"asist_{al['id']}_{fecha_str}",
                            label_visibility="collapsed"
                        )

                    if st.form_submit_button("💾 Guardar Asistencia de la Fecha"):
                        for al_id, est in estados_form.items():
                            c.execute("""
                                INSERT INTO asistencias (catedra_id, estudiante_id, fecha, estado)
                                VALUES (?, ?, ?, ?)
                                ON CONFLICT(catedra_id, estudiante_id, fecha) 
                                DO UPDATE SET estado = excluded.estado
                            """, (cat_id, al_id, fecha_str, est))
                        conn.commit()
                        st.success(f"Asistencia guardada con éxito para la fecha {fecha_str}.")
                        st.rerun()

                st.divider()
                st.markdown("### 📊 **Estadísticas Generales y Porcentaje de Asistencia**")
                
                resumen_asist = []
                for _, al in alumnos_asist.iterrows():
                    total_clases = c.execute("SELECT COUNT(*) FROM asistencias WHERE catedra_id = ? AND estudiante_id = ?", (cat_id, al['id'])).fetchone()[0]
                    total_presentes = c.execute("SELECT COUNT(*) FROM asistencias WHERE catedra_id = ? AND estudiante_id = ? AND estado = 'Presente'", (cat_id, al['id'])).fetchone()[0]
                    total_ausentes = total_clases - total_presentes
                    pct = round((total_presentes / total_clases) * 100, 1) if total_clases > 0 else 0.0

                    resumen_asist.append({
                        "Estudiante": al['nombre'],
                        "Email": al['email'],
                        "Clases Registradas": total_clases,
                        "Presentes": total_presentes,
                        "Ausentes": total_ausentes,
                        "% Asistencia": f"{pct}%"
                    })

                df_asist_resumen = pd.DataFrame(resumen_asist)
                st.dataframe(df_asist_resumen, use_container_width=True, hide_index=True)

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

    tab_al_curso, tab_al_notas, tab_al_asist = st.tabs(["📘 Curso y Evaluaciones", "📊 Mis Calificaciones", "📋 Mi Asistencia"])

    with tab_al_curso:
        df_sec_al = pd.read_sql("SELECT id, titulo FROM secciones WHERE catedra_id = ? ORDER BY orden ASC", conn, params=(materia_id,))
        for _, s in df_sec_al.iterrows():
            st.markdown(f"#### 📂 {s['titulo']}")
            acts_al = pd.read_sql("SELECT * FROM actividades WHERE seccion_id = ?", conn, params=(s['id'],))
            
            for _, act in acts_al.iterrows():
                ico = "💬" if act['tipo'] == 'Foro' else ("⏱️" if act['tipo'] == 'Cuestionario' else ("📄" if act['tipo'] == 'Tarea' else ("🎬" if es_enlace_video(act['enlace_archivo']) else "🔗")))
                
                # Renderizado específico según tipo
                if act['tipo'] == "Foro":
                    with st.expander(f"{ico} {act['titulo']} ({act['tipo']}) — Vence: {act['fecha_limite']}"):
                        st.markdown(f"**📌 Tema de debate / Consigna:**")
                        st.write(act['descripcion'])
                        
                        if act['enlace_archivo']:
                            renderizar_recurso_multimedia(act['enlace_archivo'])

                        st.divider()
                        st.markdown("#### 💬 **Hilo de Debate:**")
                        
                        mensajes_foro = pd.read_sql("""
                            SELECT m.id, m.mensaje, m.fecha, u.nombre, u.rol
                            FROM foro_mensajes m
                            JOIN usuarios u ON m.usuario_id = u.id
                            WHERE m.actividad_id = ?
                            ORDER BY m.id ASC
                        """, conn, params=(act['id'],))

                        if mensajes_foro.empty:
                            st.info("Aún no hay mensajes en este foro. ¡Sé el primero en participar!")
                        else:
                            for _, m_row in mensajes_foro.iterrows():
                                es_docente = (m_row['rol'] == 'profesor')
                                clase_css = "forum-msg-docente" if es_docente else "forum-msg-alumno"
                                badge_rol = "👨‍🏫 Docente" if es_docente else "🎓 Estudiante"
                                
                                st.markdown(f"""
                                <div class='{clase_css}'>
                                    <b>{m_row['nombre']}</b> &nbsp;<small style='color:#64748b;'>({badge_rol}) — {m_row['fecha']}</small><br>
                                    <p style='margin-top: 6px; margin-bottom: 0px;'>{m_row['mensaje']}</p>
                                </div>
                                """, unsafe_allow_html=True)

                        with st.form(f"form_responder_foro_al_{act['id']}", clear_on_submit=True):
                            txt_resp_al = st.text_area("Escribir mi aporte en el foro:", key=f"txt_foro_al_{act['id']}")
                            if st.form_submit_button("Publicar en el Foro") and txt_resp_al.strip():
                                c.execute("""
                                    INSERT INTO foro_mensajes (actividad_id, usuario_id, mensaje, fecha)
                                    VALUES (?, ?, ?, ?)
                                """, (act['id'], u['id'], txt_resp_al.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                                conn.commit()
                                st.success("Aporte publicado en el foro.")
                                st.rerun()

                else:
                    ent_al = pd.read_sql("SELECT * FROM entregas WHERE actividad_id = ? AND estudiante_id = ?", conn, params=(act['id'], u['id']))
                    ya_rendido = not ent_al.empty
                    
                    with st.expander(f"{ico} {act['titulo']} ({act['tipo']}) | {'✅ Completado' if ya_rendido else '⏳ Pendiente'}"):
                        st.write(f"**Consigna:** {act['descripcion']}")
                        
                        if act['enlace_archivo']:
                            renderizar_recurso_multimedia(act['enlace_archivo'])

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
                                            num_p = idx + 1
                                            t_p = p.get("tipo", "multiple_choice")
                                            
                                            if t_p == "multiple_choice":
                                                st.markdown(f"**Pregunta N° {num_p} (Opción Múltiple):** {p['enunciado']}")
                                                rtas_seleccionadas[idx] = st.radio("Seleccioná la respuesta:", p['opciones'], key=f"ans_{act['id']}_{idx}")
                                            
                                            elif t_p == "verdadero_falso":
                                                st.markdown(f"**Pregunta N° {num_p} (Verdadero / Falso):** {p['enunciado']}")
                                                rtas_seleccionadas[idx] = st.radio("¿Es verdadero o falso?:", p['opciones'], horizontal=True, key=f"ans_vf_{act['id']}_{idx}")

                                            elif t_p == "completar_espacios":
                                                st.markdown(f"**Pregunta N° {num_p} (Completar Párrafo):**")
                                                correctas = p['palabras_correctas']
                                                banco_palabras = list(set(correctas + p.get('distractores', [])))
                                                
                                                st.markdown("🎯 **Banco de palabras disponibles:** " + " ".join([f"<span class='drag-word-box'>{w}</span>" for w in banco_palabras]), unsafe_allow_html=True)
                                                
                                                texto_limpio = p['enunciado']
                                                for cor in correctas:
                                                    texto_limpio = texto_limpio.replace(f"[{cor}]", " `[ _____ ]` ")
                                                st.markdown(f"> *{texto_limpio}*")
                                                
                                                resp_gaps = {}
                                                cols_gaps = st.columns(len(correctas))
                                                for g_idx, cor in enumerate(correctas):
                                                    with cols_gaps[g_idx]:
                                                        resp_gaps[f"gap_{g_idx}"] = st.selectbox(f"Espacio #{g_idx+1}:", ["(Seleccionar palabra)"] + banco_palabras, key=f"gap_{act['id']}_{idx}_{g_idx}")
                                                
                                                rtas_seleccionadas[idx] = resp_gaps

                                        if st.form_submit_button("Terminar y Enviar Examen") or t_restante == 0:
                                            puntos = 0
                                            total_puntos = len(pregs)
                                            
                                            for idx, p in enumerate(pregs):
                                                t_p = p.get("tipo", "multiple_choice")
                                                if t_p in ["multiple_choice", "verdadero_falso"]:
                                                    if rtas_seleccionadas.get(idx) == p['correcta']:
                                                        puntos += 1
                                                elif t_p == "completar_espacios":
                                                    correctas = p['palabras_correctas']
                                                    gaps_al = rtas_seleccionadas.get(idx, {})
                                                    aciertos_gaps = sum(1 for g_idx, cor in enumerate(correctas) if gaps_al.get(f"gap_{g_idx}") == cor)
                                                    puntos += (aciertos_gaps / len(correctas)) if correctas else 1
                                            
                                            nota_calc = round((puntos / total_puntos) * 10, 2) if total_puntos > 0 else 10.0
                                            dev_auto = f"Autocorrección del sistema: Calificación obtenida {nota_calc}/10."
                                            
                                            c.execute("""
                                                INSERT INTO entregas (actividad_id, estudiante_id, fecha_entrega, respuesta_data, nota, devolucion, tiempo_empleado_seg)
                                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                            """, (act['id'], u['id'], datetime.now().strftime("%Y-%m-%d %H:%M"), json.dumps(rtas_seleccionadas, ensure_ascii=False), nota_calc, dev_auto, t_pasado))
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

    with tab_al_asist:
        st.markdown("### **Mi Registro de Asistencia**")
        df_mis_asist = pd.read_sql("""
            SELECT fecha as 'Fecha de Clase', estado as 'Estado'
            FROM asistencias 
            WHERE catedra_id = ? AND estudiante_id = ?
            ORDER BY fecha DESC
        """, conn, params=(materia_id, u['id']))

        if df_mis_asist.empty:
            st.info("No hay registros de asistencia en esta materia todavía.")
        else:
            total = len(df_mis_asist)
            presentes = len(df_mis_asist[df_mis_asist['Estado'] == 'Presente'])
            porcentaje = round((presentes / total) * 100, 1)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Clases", total)
            c2.metric("Clases Presente", presentes)
            c3.metric("% Asistencia", f"{porcentaje}%")
            
            st.dataframe(df_mis_asist, use_container_width=True, hide_index=True)
