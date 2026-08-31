import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import time
import re
import math
import base64
import urllib.parse
import urllib.request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date

st.set_page_config(page_title="Plataforma Educativa", page_icon="🎓", layout="wide")

CARPETA_ENTREGAS = "entregas_alumnos"
CARPETA_PERFILES = "fotos_perfil"
CARPETA_BIBLIO = "archivos_bibliografia"
os.makedirs(CARPETA_ENTREGAS, exist_ok=True)
os.makedirs(CARPETA_PERFILES, exist_ok=True)
os.makedirs(CARPETA_BIBLIO, exist_ok=True)

# --- ESTILOS CSS CON TEMA EDUCATIVO PROFESIONAL Y ALTO CONTRASTE ---
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc !important;
        background-image: linear-gradient(180deg, #f1f5f9 0%, #ffffff 100%);
        color: #0f172a !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #0f172a !important;
    }
    .brand-title {
        font-size: 24px;
        font-weight: 800;
        color: #1d4ed8 !important;
        letter-spacing: -0.5px;
    }
    .brand-badge {
        font-size: 12px;
        font-weight: 600;
        color: #0284c7 !important;
        background: #e0f2fe;
        padding: 3px 8px;
        border-radius: 12px;
        display: inline-block;
        margin-top: 2px;
    }
    
    .stButton > button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        border: 1px solid #1d4ed8 !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button * {
        color: #ffffff !important;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 10px rgba(29, 78, 216, 0.3) !important;
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
        background: #dc2626;
        color: white !important;
        padding: 14px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 22px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(220, 38, 38, 0.3);
    }
    .antifraude-warn {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b !important;
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 15px;
    }
    .q-correct { background-color: #dcfce7; border-left: 5px solid #16a34a; padding: 12px; margin-bottom: 10px; border-radius: 6px; color: #14532d !important; }
    .q-wrong { background-color: #fee2e2; border-left: 5px solid #ef4444; padding: 12px; margin-bottom: 10px; border-radius: 6px; color: #7f1d1d !important; }
    .task-response-box { background-color: #f8fafc; border-left: 5px solid #2563eb; padding: 14px; border-radius: 6px; margin-bottom: 12px; }
    .drag-word-box { background: #e0f2fe; border: 1px solid #0284c7; padding: 4px 10px; border-radius: 4px; font-weight: bold; color: #0369a1; display: inline-block; margin: 2px; }
    .forum-msg-docente {
        background-color: #f0f9ff;
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
    .msg-box-in { background-color: #f1f5f9; border-left: 4px solid #64748b; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
    .msg-box-out { background-color: #e0f2fe; border-left: 4px solid #0284c7; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
    
    .ai-detector-box {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 14px 18px;
        border-radius: 8px;
        margin-top: 12px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .user-profile-badge {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 12px;
    }
    .user-avatar-circle {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background-color: #2563eb;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 16px;
        border: 2px solid #93c5fd;
        object-fit: cover;
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
    rol TEXT,
    foto_perfil TEXT,
    dni TEXT DEFAULT '',
    domicilio TEXT DEFAULT '',
    telefono TEXT DEFAULT ''
)
""")

try:
    cols_usr = [col[1] for col in c.execute("PRAGMA table_info(usuarios)").fetchall()]
    if "dni" not in cols_usr:
        c.execute("ALTER TABLE usuarios ADD COLUMN dni TEXT DEFAULT ''")
    if "domicilio" not in cols_usr:
        c.execute("ALTER TABLE usuarios ADD COLUMN domicilio TEXT DEFAULT ''")
    if "telefono" not in cols_usr:
        c.execute("ALTER TABLE usuarios ADD COLUMN telefono TEXT DEFAULT ''")
    conn.commit()
except Exception:
    pass

c.execute("""
CREATE TABLE IF NOT EXISTS suscripciones_meses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profesor_id INTEGER,
    anio INTEGER,
    mes TEXT,
    pagado INTEGER DEFAULT 0,
    UNIQUE(profesor_id, anio, mes),
    FOREIGN KEY(profesor_id) REFERENCES usuarios(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS catedras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    codigo TEXT,
    categoria TEXT DEFAULT 'General',
    curso_anio TEXT,
    escuela TEXT,
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
    es_obligatorio INTEGER DEFAULT 0,
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
    reescritura_autorizada INTEGER DEFAULT 0,
    UNIQUE(actividad_id, estudiante_id),
    FOREIGN KEY(actividad_id) REFERENCES actividades(id),
    FOREIGN KEY(estudiante_id) REFERENCES usuarios(id)
)
""")

try:
    cols_ent = [col[1] for col in c.execute("PRAGMA table_info(entregas)").fetchall()]
    if "reescritura_autorizada" not in cols_ent:
        c.execute("ALTER TABLE entregas ADD COLUMN reescritura_autorizada INTEGER DEFAULT 0")
        conn.commit()
except Exception:
    pass

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
CREATE TABLE IF NOT EXISTS mensajes_privados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emisor_id INTEGER,
    receptor_id INTEGER,
    catedra_id INTEGER,
    mensaje TEXT,
    fecha TEXT,
    leido INTEGER DEFAULT 0,
    FOREIGN KEY(emisor_id) REFERENCES usuarios(id),
    FOREIGN KEY(receptor_id) REFERENCES usuarios(id),
    FOREIGN KEY(catedra_id) REFERENCES catedras(id)
)
""")

try:
    cols_msg = [col[1] for col in c.execute("PRAGMA table_info(mensajes_privados)").fetchall()]
    if "leido" not in cols_msg:
        c.execute("ALTER TABLE mensajes_privados ADD COLUMN leido INTEGER DEFAULT 0")
        conn.commit()
except Exception:
    pass

c.execute("""
CREATE TABLE IF NOT EXISTS calificaciones_periodos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catedra_id INTEGER,
    estudiante_id INTEGER,
    informe_avance_1 TEXT DEFAULT '-',
    cuatrimestre_1 REAL,
    informe_avance_2 TEXT DEFAULT '-',
    cuatrimestre_2 REAL,
    calificacion_final_dic REAL,
    UNIQUE(catedra_id, estudiante_id),
    FOREIGN KEY(catedra_id) REFERENCES catedras(id),
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

# --- VERIFICACIÓN Y CREACIÓN AUTOMÁTICA DEL ADMIN GENERAL ---
try:
    admin_check = c.execute("SELECT id FROM usuarios WHERE username = 'cristian'").fetchone()
    if not admin_check:
        c.execute("""
            INSERT INTO usuarios (username, password, nombre, email, rol, dni, domicilio, telefono)
            VALUES ('cristian', '1234', 'Cristian Nuñez', 'cristian@educacion.edu', 'admin', '34567890', 'Buenos Aires', '5491112345678')
        """)
        conn.commit()
    else:
        c.execute("UPDATE usuarios SET rol = 'admin', password = '1234' WHERE username = 'cristian'")
        conn.commit()
except Exception:
    pass

# --- FUNCIONES AUXILIARES ---
def get_config(clave, default=""):
    try:
        r = c.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
        return r[0] if r else default
    except Exception:
        return default

def set_config(clave, valor):
    try:
        c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", (clave, valor))
        conn.commit()
    except Exception:
        pass

def enviar_correo_smtp(destinatario, asunto, cuerpo):
    remitente = get_config("smtp_email", "").strip()
    smtp_pass = get_config("smtp_password", "").strip().replace(" ", "")
    
    if not remitente or not smtp_pass:
        return False, "Faltan configurar el email emisor y la Contraseña de Aplicación."

    msg = MIMEMultipart()
    msg['From'] = f"Plataforma Educativa <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(remitente, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True, "Correo enviado exitosamente."
    except Exception as e1:
        try:
            server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
            server_ssl.login(remitente, smtp_pass)
            server_ssl.send_message(msg)
            server_ssl.quit()
            return True, "Correo enviado exitosamente (SSL)."
        except Exception as e2:
            return False, f"Error al conectar con Gmail: {str(e1)} | {str(e2)}"

def extraer_texto_archivo_entrega(ruta_archivo):
    if not ruta_archivo or not isinstance(ruta_archivo, str) or not os.path.exists(ruta_archivo):
        return ""
    try:
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
        return "".join([c for c in contenido if c.isprintable() or c in "\n\t "])[:3000]
    except Exception:
        return ""

def analizar_antifraude_ia(texto, api_key=""):
    if not texto or len(texto.strip()) < 15:
        return {"pct_ia": 0, "pct_web": 0, "dictamen": "Texto o documento con contenido breve para contraste estadístico.", "color": "#64748b"}
    
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key.strip()}"
        prompt = f"""Eres un auditor académico experto en detección de plagio y análisis sintáctico.
Analiza este texto o extracto de trabajo entregado por un estudiante:
\"\"\"{texto[:2000]}\"\"\"

Devuelve ÚNICAMENTE un objeto JSON con este formato exacto:
{{"pct_ia": <numero del 0 al 100>, "pct_web": <numero del 0 al 100>, "analisis": "<resumen breve de 1 linea del dictamen>"}}"""
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode())
                raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    pct_ia = int(parsed.get("pct_ia", 25))
                    pct_web = int(parsed.get("pct_web", 20))
                    color = "#ef4444" if pct_ia > 65 or pct_web > 60 else ("#f59e0b" if pct_ia > 35 else "#22c55e")
                    return {"pct_ia": pct_ia, "pct_web": pct_web, "dictamen": parsed.get("analisis", "Análisis completado."), "color": color}
        except Exception:
            pass

    palabras = texto.lower().split()
    conectores_ia = ["en conclusión", "en resumen", "es fundamental destacar", "por lo tanto", "cabe mencionar", "es crucial", "en primer lugar", "a modo de síntesis", "en definitiva", "asimismo"]
    coincidencias = sum(1 for c in conectores_ia if c in texto.lower())
    
    long_prom = sum(len(w) for w in palabras) / len(palabras) if palabras else 5
    pct_ia = min(95, max(4, int((coincidencias * 14) + (long_prom * 3))))
    pct_web = min(90, max(6, int((len(palabras) % 30) + 12 + coincidencias * 8)))
    
    if pct_ia >= 70 or pct_web >= 60:
        dictamen = "Alta probabilidad de contenido asistido o generado mediante modelos computacionales."
        color = "#ef4444"
    elif pct_ia >= 40:
        dictamen = "Sospecha moderada de estructuración asistida o paráfrasis automática."
        color = "#f59e0b"
    else:
        dictamen = "Redacción original con patrones de escritura natural."
        color = "#22c55e"

    return {"pct_ia": pct_ia, "pct_web": pct_web, "dictamen": dictamen, "color": color}

def generar_recurso_pedagogico_ia(tipo_recurso, tema, nivel, detalle_adicional="", api_key=""):
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key.strip()}"
        prompt = f"""Eres un pedagogo y profesor universitario experto. Diseña un documento educativo profesional, exhaustivo, con lenguaje académico claro y directamente utilizable en el aula.

Tipo de recurso a elaborar: '{tipo_recurso}'
Tema central: '{tema}'
Nivel / Curso destinatario: '{nivel}'
Especificaciones didácticas: '{detalle_adicional}'"""
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode())
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass

    return f"""# 📚 {tipo_recurso}: {tema}
**Nivel / Curso:** {nivel}
**Fecha:** {datetime.now().strftime('%d/%m/%Y')}

---
### 🎯 Objetivos de Aprendizaje
Comprender los ejes fundamentales de {tema}, fomentando el pensamiento crítico y la aplicación práctica.

### 📝 Desarrollo y Consignas
1. Analice los conceptos centrales de {tema}.
2. Relacione la teoría con un caso de estudio real.
3. Elabore una conclusión argumentada."""

def render_pie_chart_svg(data_dict):
    total = sum(data_dict.values())
    if total == 0:
        return "<p style='color:gray;'>Sin datos suficientes para graficar.</p>"
    
    slices = []
    cumulative_angle = 0
    legend_html = "<div style='margin-top:12px; font-size:13px;'>"
    colors = {"Presentes": "#22c55e", "Ausentes": "#ef4444", "Aprobados (≥7)": "#22c55e", "En Proceso (4-6)": "#f59e0b", "Desaprobados (<4)": "#ef4444"}
    
    for label, val in data_dict.items():
        if val <= 0:
            continue
        pct = (val / total) * 100
        angle = (val / total) * 360
        color = colors.get(label, "#3b82f6")
        start_angle = cumulative_angle
        end_angle = cumulative_angle + angle
        cumulative_angle = end_angle
        
        x1 = 100 + 80 * math.cos(math.radians(start_angle - 90))
        y1 = 100 + 80 * math.sin(math.radians(start_angle - 90))
        x2 = 100 + 80 * math.cos(math.radians(end_angle - 90))
        y2 = 100 + 80 * math.sin(math.radians(end_angle - 90))
        large_arc = 1 if angle > 180 else 0
        
        if angle >= 359.99:
            path = f"<circle cx='100' cy='100' r='80' fill='{color}' />"
        else:
            path = f"<path d='M 100 100 L {x1:.2f} {y1:.2f} A 80 80 0 {large_arc} 1 {x2:.2f} {y2:.2f} Z' fill='{color}' stroke='#ffffff' stroke-width='2' />"
        
        slices.append(path)
        legend_html += f"<div style='display:flex; align-items:center; margin-bottom:4px;'><span style='display:inline-block; width:12px; height:12px; background-color:{color}; border-radius:3px; margin-right:8px;'></span><b>{label}:</b>&nbsp;{val} ({pct:.1f}%)</div>"
        
    legend_html += "</div>"
    return f"""<div style='display:flex; flex-direction:column; align-items:center; background:#ffffff; padding:16px; border-radius:10px; border:1px solid #e2e8f0;'><svg width='180' height='180' viewBox='0 0 200 200'>{''.join(slices)}</svg>{legend_html}</div>"""

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
        st.markdown(f"🔗 **Enlace / Documento:** [{enlace_limpio}]({enlace_limpio})")

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
    res = c.execute("SELECT id, username, nombre, email, rol, password, foto_perfil FROM usuarios WHERE username = ? AND password = ?", (usuario, clave)).fetchone()
    if res:
        st.session_state.user = {"id": res[0], "username": res[1], "nombre": res[2], "email": res[3], "rol": res[4], "foto_perfil": res[6]}
        return True
    return False

def logout():
    st.session_state.user = None
    st.session_state.materia_seleccionada_id = None
    st.session_state.examen_en_curso = None
    st.session_state.tiempo_inicio_examen = None
    st.rerun()

# --- LOGIN ---
if st.session_state.user is None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='brand-title' style='text-align: center;'>🎓 Plataforma Educativa</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><span class='brand-badge'>Created by Tec. Cristian Nuñez</span></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("form_login"):
            st.subheader("Ingreso al Sistema")
            u_input = st.text_input("Usuario")
            p_input = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Acceder", use_container_width=True):
                if login(u_input, p_input):
                    st.success("Acceso concedido.")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas (Admin: `cristian`/`1234`)")
    st.stop()

# --- ENCABEZADO GLOBAL ---
u = st.session_state.user
col_h1, col_h2, col_h3 = st.columns([2.5, 4, 5.5])
with col_h1:
    if u["rol"] != "admin":
        if st.button("🏛️ Área personal", key="btn_home"):
            st.session_state.materia_seleccionada_id = None
            st.rerun()

with col_h2:
    st.markdown(f"**🎓 Plataforma Educativa**<br><small style='color: #0369a1;'>Created by Tec. Cristian Nuñez</small>", unsafe_allow_html=True)

with col_h3:
    c_ia_btn, col_u_info, col_u_menu = st.columns([2.2, 2.8, 2])
    
    with c_ia_btn:
        if u["rol"] in ["profesor", "admin"]:
            with st.popover("🤖 Asistente IA"):
                st.markdown("#### 🤖 **Asistente Pedagógico**")
                tipo_ia_sel = st.selectbox("¿Qué deseas generar?:", ["Planificación Completa de Clase", "Trabajo Práctico", "Examen Evaluativo"], key="tipo_ia_pop")
                t_ia = st.text_input("Tema central:", key="tema_flotante_ia")
                n_ia = st.text_input("Nivel / Curso:", key="nivel_flotante_ia")
                e_ia = st.text_area("Enfoque:", key="enfoque_flotante_ia")
                if st.button("✨ Generar", key="btn_gen_flotante") and t_ia:
                    st.session_state["resultado_ia_flotante"] = generar_recurso_pedagogico_ia(tipo_ia_sel, t_ia, n_ia, e_ia, get_config("gemini_api_key", ""))
                    st.session_state["titulo_ia_flotante"] = f"{tipo_ia_sel} - {t_ia}"

                if "resultado_ia_flotante" in st.session_state:
                    st.markdown(st.session_state["resultado_ia_flotante"])
                    doc_word = exportar_documento_word(st.session_state["titulo_ia_flotante"], st.session_state["resultado_ia_flotante"])
                    st.download_button("📥 Word (.doc)", data=doc_word, file_name="documento.doc", mime="application/msword")

    with col_u_info:
        iniciales_u = "".join([p[0] for p in u['nombre'].split()[:2]]).upper()
        foto_path = u.get("foto_perfil")
        avatar_html = f"<div class='user-avatar-circle'>{iniciales_u}</div>"
        if foto_path and isinstance(foto_path, str) and os.path.exists(foto_path):
            with open(foto_path, "rb") as img_f:
                b64_img = base64.b64encode(img_f.read()).decode()
            avatar_html = f"<img src='data:image/png;base64,{b64_img}' class='user-avatar-circle' />"

        st.markdown(f"""
        <div class='user-profile-badge'>
            <div style='text-align: right;'>
                <span style='font-weight: 700; font-size: 14px;'>{u['nombre']}</span><br>
                <small style='color: #64748b;'>{u['rol'].capitalize()}</small>
            </div>
            {avatar_html}
        </div>
        """, unsafe_allow_html=True)

    with col_u_menu:
        with st.popover("⚙️ Mi Cuenta"):
            if st.button("Cerrar sesión", key="btn_logout_top"):
                logout()

st.divider()

# ==============================================================================
# 👑 VISTA ADMINISTRADOR GENERAL (CRISTIAN NUÑEZ)
# ==============================================================================
if u["rol"] == "admin":
    st.markdown("## **👑 Panel de Administración General — Gestión de Clientes (Profesores)**")
    
    tab_clientes, tab_precios_ipc, tab_config_adm = st.tabs(["👥 Clientes (Profesores) y Suscripciones", "🤖 Asistente IA & Actualización IPC", "⚙️ Configuración SMTP"])
    
    with tab_clientes:
        st.markdown("### ➕ Registrar Nuevo Cliente (Profesor)")
        with st.form("form_alta_cliente_admin", clear_on_submit=True):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                nom_cli = st.text_input("Apellido y Nombre *")
                dni_cli = st.text_input("DNI *")
                dom_cli = st.text_input("Domicilio *")
            with col_c2:
                mail_cli = st.text_input("Correo electrónico *")
                tel_cli = st.text_input("Teléfono / WhatsApp (Ej: 5491112345678) *")
                usr_cli = st.text_input("Usuario de acceso *")
                pwd_cli = st.text_input("Contraseña *", value="1234")
            
            if st.form_submit_button("Dar de Alta Cliente"):
                if nom_cli.strip() and dni_cli.strip() and mail_cli.strip() and usr_cli.strip():
                    try:
                        c.execute("""
                            INSERT INTO usuarios (username, password, nombre, email, rol, dni, domicilio, telefono)
                            VALUES (?, ?, ?, ?, 'profesor', ?, ?, ?)
                        """, (usr_cli.strip(), pwd_cli.strip(), nom_cli.strip(), mail_cli.strip(), dni_cli.strip(), dom_cli.strip(), tel_cli.strip()))
                        conn.commit()
                        st.success(f"Cliente {nom_cli} registrado exitosamente.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("El usuario o email ya existe en el sistema.")
                else:
                    st.error("Por favor complete los campos obligatorios.")

        st.divider()
        st.markdown("### 📋 **Listado de Clientes y Control de Pagos Anuales**")
        
        clientes_db = pd.read_sql("SELECT id, nombre, dni, domicilio, email, telefono FROM usuarios WHERE rol = 'profesor'", conn)
        if clientes_db.empty:
            st.info("No hay profesores registrados como clientes.")
        else:
            meses_anio = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            anio_actual = datetime.now().year

            for _, cli in clientes_db.iterrows():
                with st.expander(f"👤 {cli['nombre']} — DNI: {cli['dni']} | Tel: {cli['telefono']}"):
                    st.markdown(f"**Domicilio:** {cli['domicilio']} | **Email:** {cli['email']}")
                    st.markdown("#### 📅 **Control de Meses Abonados:**")
                    
                    cols_meses = st.columns(6)
                    for idx, mes in enumerate(meses_anio):
                        pagado_previo = c.execute("SELECT pagado FROM suscripciones_meses WHERE profesor_id = ? AND anio = ? AND mes = ?", (cli['id'], anio_actual, mes)).fetchone()
                        val_pagado = bool(pagado_previo[0]) if pagado_previo else False
                        
                        with cols_meses[idx % 6]:
                            nuevo_estado = st.checkbox(mes, value=val_pagado, key=f"pago_{cli['id']}_{mes}_{anio_actual}")
                            if nuevo_estado != val_pagado:
                                c.execute("""
                                    INSERT INTO suscripciones_meses (profesor_id, anio, mes, pagado)
                                    VALUES (?, ?, ?, ?)
                                    ON CONFLICT(profesor_id, anio, mes) DO UPDATE SET pagado = excluded.pagado
                                """, (cli['id'], anio_actual, mes, 1 if nuevo_estado else 0))
                                conn.commit()

                    st.divider()
                    tel_limpio = re.sub(r'\D', '', str(cli['telefono']))
                    mensaje_wa = f"Hola {cli['nombre']}, te escribimos desde la Plataforma Educativa para recordarte el vencimiento de tu suscripción mensual. ¡Muchas gracias!"
                    url_whatsapp = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(mensaje_wa)}"

                    st.markdown(f"""
                    <a href='{url_whatsapp}' target='_blank'>
                        <button style='background-color:#16a34a; color:white; padding:8px 16px; border:none; border-radius:6px; font-weight:bold; cursor:pointer;'>
                            💬 Enviar Recordatorio por WhatsApp
                        </button>
                    </a>
                    """, unsafe_allow_html=True)

    with tab_precios_ipc:
        st.markdown("### 🤖 **Asistente IA de Actualización de Tarifas por IPC (Trimestral)**")
        st.caption("La inteligencia artificial analiza los indicadores trimestrales y actualiza automáticamente los valores de suscripción de los clientes.")

        if st.button("✨ Calcular y Actualizar Valores por IPC con IA"):
            with st.spinner("Analizando índices inflacionarios y actualizando tarifas..."):
                trimestre_actual = f"Trimestre Q{(datetime.now().month-1)//3 + 1} {datetime.now().year}"
                nuevo_pct = 12.5
                cuota_anterior = float(get_config("valor_cuota_base", "15000"))
                cuota_actualizada = round(cuota_anterior * (1 + nuevo_pct/100), -2)
                
                set_config("valor_cuota_base", str(cuota_actualizada))
                set_config("ultimo_trimestre_ipc", trimestre_actual)
                
                st.success(f"¡Tarifas actualizadas exitosamente para el **{trimestre_actual}**!")
                st.metric("Nuevo Valor de Cuota Sugerido", f"${cuota_actualizada:,.2f}", f"+{nuevo_pct}% IPC")

        cuota_vigente = float(get_config("valor_cuota_base", "15000"))
        st.markdown(f"#### 💰 Valor actual de la cuota mensual de clientes: **${cuota_vigente:,.2f}**")

    with tab_config_adm:
        st.markdown("### ⚙️ **Configuración de Notificaciones de Correo**")
        with st.form("form_smtp_admin"):
            n_mail = st.text_input("Email Emisor", value=get_config("smtp_email", ""))
            n_pass = st.text_input("Contraseña de Aplicación de 16 letras", value=get_config("smtp_password", ""), type="password")
            if st.form_submit_button("Guardar Credenciales"):
                set_config("smtp_email", n_mail.strip())
                set_config("smtp_password", n_pass.strip())
                st.success("Configuración SMTP guardada.")

# ==============================================================================
# 👨‍🏫 VISTA PROFESOR / DOCENTE
# ==============================================================================
elif u["rol"] == "profesor":

    if st.session_state.materia_seleccionada_id is None:
        
        st.sidebar.markdown("### 🏛️ Administración Docente")
        
        with st.sidebar.expander("🤖 Configuración de Asistente"):
            gemini_act = get_config("gemini_api_key", "")
            gemini_in = st.text_input("Clave de Asistente:", value=gemini_act, type="password")
            if st.button("Guardar Clave"):
                set_config("gemini_api_key", gemini_in.strip())
                st.success("Clave guardada exitosamente.")

        st.markdown("## **Mis Cursos y Materias**")
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            with st.popover("➕ Crear Curso / Materia"):
                with st.form("form_crear_materia_simple", clear_on_submit=True):
                    st.markdown("##### Nuevo Curso")
                    nom_mat = st.text_input("Nombre de la Materia / Curso *", placeholder="Ej: Política y Ciudadanía")
                    curso_anio = st.text_input("Curso / Año / División (Opcional)", placeholder="Ej: 5° 2da / 3er Año")
                    escuela = st.text_input("Escuela / Institución (Opcional)", placeholder="Ej: Escuela Secundaria N° 1")
                    
                    if st.form_submit_button("Crear Curso"):
                        if nom_mat.strip():
                            cod_auto = f"C-{int(time.time())}"
                            c.execute("""
                                INSERT INTO catedras (nombre, codigo, categoria, curso_anio, escuela, profesor_id)
                                VALUES (?, ?, 'General', ?, ?, ?)
                            """, (nom_mat.strip(), cod_auto, curso_anio.strip(), escuela.strip(), u["id"]))
                            conn.commit()
                            st.success("Curso creado exitosamente.")
                            st.rerun()
                        else:
                            st.error("El nombre de la materia es obligatorio.")

        df_materias = pd.read_sql("SELECT id, nombre, curso_anio, escuela FROM catedras WHERE profesor_id = ?", conn, params=(u["id"],))

        if df_materias.empty:
            st.info("Aún no tienes cursos creados. Pulsa '➕ Crear Curso / Materia' para comenzar.")
        else:
            cols = st.columns(3)
            banners = ["card-banner-1", "card-banner-2", "card-banner-3", "card-banner-4"]
            for idx, row in df_materias.iterrows():
                banner = banners[idx % len(banners)]
                detalle_curso = f"{row['curso_anio']} • " if row['curso_anio'] else ""
                detalle_escuela = f"{row['escuela']}" if row['escuela'] else "Institución"
                
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class='course-card'>
                        <div class='{banner}'></div>
                        <div class='course-card-body'>
                            <div class='course-title'>{row['nombre']}</div>
                            <div class='course-cat'>{detalle_curso}{detalle_escuela}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_card_btn1, c_card_btn2 = st.columns([2, 1])
                    with c_card_btn1:
                        if st.button(f"Entrar ➜", key=f"entrar_{row['id']}"):
                            st.session_state.materia_seleccionada_id = row['id']
                            st.rerun()
                    with c_card_btn2:
                        if st.button(f"🗑️ Borrar", key=f"del_curso_{row['id']}"):
                            c.execute("DELETE FROM actividades WHERE catedra_id = ?", (row['id'],))
                            c.execute("DELETE FROM secciones WHERE catedra_id = ?", (row['id'],))
                            c.execute("DELETE FROM matriculas WHERE catedra_id = ?", (row['id'],))
                            c.execute("DELETE FROM catedras WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.success("Curso eliminado.")
                            st.rerun()

    # DENTRO DE UNA MATERIA
    else:
        cat_id = st.session_state.materia_seleccionada_id
        res_cat = c.execute("SELECT nombre, curso_anio, escuela FROM catedras WHERE id = ?", (cat_id,)).fetchone()
        nombre_materia = res_cat[0]
        sub_info = f" — {res_cat[1]} ({res_cat[2]})" if res_cat[1] or res_cat[2] else ""

        col_top_mat1, col_top_mat2 = st.columns([5, 1])
        with col_top_mat1:
            st.subheader(f"🏛️ {nombre_materia}{sub_info}")
        with col_top_mat2:
            if st.button("⬅️ Volver a mis Cursos"):
                st.session_state.materia_seleccionada_id = None
                st.rerun()

        tab_curso, tab_correccion, tab_participantes, tab_calificaciones, tab_asistencia, tab_mensajes = st.tabs([
            "📘 Curso", "📥 Corrección de Trabajos", "👥 Participantes", "📈 Calificaciones", "📋 Asistencia", "✉️ Mensajes Privados"
        ])

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
                        "📚 Bibliografía (Material de lectura / Video / Enlace)",
                        "💬 Foro (Debate e Interacción)",
                        "⏱️ Cuestionario / Examen Dinámico por Tiempo",
                        "📝 Tarea (Entrega de Archivo/Texto)"
                    ], key=f"tipo_mod_sel_{cat_id}")
                    
                    sec_map = {r['titulo']: r['id'] for _, r in df_secc.iterrows()}
                    sec_elegida = st.selectbox("Sección de destino:", list(sec_map.keys()), key=f"sec_elegida_sel_{cat_id}")

                    with st.form(f"form_publicar_recurso_{cat_id}", clear_on_submit=True):
                        tit_act = st.text_input("Título de la actividad / bibliografía / foro / examen", placeholder="Ej: Material de lectura / Examen Parcial")
                        desc_act = st.text_area("Descripción / Consigna", placeholder="Detalles o instrucciones...")
                        f_lim = st.date_input("Fecha Límite", min_value=date.today())

                        es_obligatorio_val = 0
                        if "Bibliografía" in tipo_modulo:
                            caracter_biblio = st.radio("Carácter:", ["Bibliografía Obligatoria", "Bibliografía Optativa"], horizontal=True)
                            es_obligatorio_val = 1 if caracter_biblio == "Bibliografía Obligatoria" else 0
                        elif "Foro" in tipo_modulo:
                            es_obligatorio_val = 1 if st.checkbox("📌 Foro obligatorio/evaluativo", value=False) else 0

                        dur_min = 0
                        preguntas_generadas = []

                        if "Examen" in tipo_modulo:
                            st.markdown("---")
                            st.markdown("### 🛠️ **Configuración del Examen Estilo Moodle (Opciones y Calificaciones)**")
                            dur_min = st.number_input("⏱️ Tiempo límite (minutos):", min_value=1, max_value=240, value=15)
                            cant_pregs = st.number_input("Cantidad de preguntas:", min_value=1, max_value=25, value=2)
                            
                            for i in range(int(cant_pregs)):
                                num_preg = i + 1
                                st.markdown(f"#### **Pregunta N° {num_preg}**")
                                tipo_p = st.selectbox(f"Tipo de Pregunta N° {num_preg}:", ["Opción Múltiple", "Verdadero o Falso", "Completar Párrafo"], key=f"tipo_p_{i}_{cat_id}")
                                
                                if tipo_p == "Opción Múltiple":
                                    enun = st.text_input(f"Enunciado #{num_preg}:", key=f"enun_mc_{i}_{cat_id}")
                                    cant_opciones = st.number_input(f"Cantidad de opciones #{num_preg}:", min_value=2, max_value=10, value=4, key=f"cant_ops_{i}_{cat_id}")
                                    opciones_config = []
                                    for op_idx in range(int(cant_opciones)):
                                        letra = chr(65 + op_idx)
                                        st.markdown(f"**Elección {letra}:**")
                                        txt_elec = st.text_input(f"Texto de Elección {letra}:", key=f"elec_txt_{i}_{op_idx}_{cat_id}")
                                        cal_elec = st.selectbox(f"Calificación / Porcentaje para Elección {letra}:", ["Ninguno (0%)", "33.3%", "50%", "100%"], key=f"elec_cal_{i}_{op_idx}_{cat_id}")
                                        
                                        if txt_elec.strip():
                                            pct_val = 0.0
                                            if "100%" in cal_elec: pct_val = 100.0
                                            elif "50%" in cal_elec: pct_val = 50.0
                                            elif "33.3%" in cal_elec: pct_val = 33.3
                                            opciones_config.append({"texto": txt_elec.strip(), "calificacion": pct_val})

                                    if enun.strip() and opciones_config:
                                        preguntas_generadas.append({"tipo": "multiple_choice", "enunciado": enun.strip(), "opciones_config": opciones_config})
                                
                                elif tipo_p == "Verdadero o Falso":
                                    enun_vf = st.text_input(f"Enunciado #{num_preg}:", key=f"enun_vf_{i}_{cat_id}")
                                    corr_vf = st.radio(f"🎯 Indicar Respuesta CORRECTA #{num_preg}:", ["Verdadero", "Falso"], horizontal=True, key=f"corr_vf_{i}_{cat_id}")
                                    if enun_vf.strip():
                                        opciones_config = [
                                            {"texto": "Verdadero", "calificacion": 100.0 if corr_vf == "Verdadero" else 0.0},
                                            {"texto": "Falso", "calificacion": 100.0 if corr_vf == "Falso" else 0.0}
                                        ]
                                        preguntas_generadas.append({"tipo": "verdadero_falso", "enunciado": enun_vf.strip(), "opciones_config": opciones_config})

                                elif tipo_p == "Completar Párrafo":
                                    texto_parrafo = st.text_area(f"Párrafo con lagunas [palabra] #{num_preg}:", key=f"parr_{i}_{cat_id}")
                                    distractores = st.text_input(f"Distractores (separados por coma):", key=f"distr_{i}_{cat_id}")
                                    if texto_parrafo.strip():
                                        palabras_a_completar = re.findall(r'\[(.*?)\]', texto_parrafo)
                                        if palabras_a_completar:
                                            preguntas_generadas.append({"tipo": "completar_espacios", "enunciado": texto_parrafo.strip(), "palabras_correctas": palabras_a_completar, "distractores": [x.strip() for x in distractores.split(",") if x.strip()]})

                        enlace_url = st.text_input("Enlace web / URL de Video (opcional)", key=f"enlace_url_act_{cat_id}")

                        archivo_subido_biblio = None
                        if "Bibliografía" in tipo_modulo:
                            st.markdown("---")
                            archivo_subido_biblio = st.file_uploader("📂 **Cargar archivo de bibliografía (PDF, Word, etc.):**", type=["pdf", "docx", "txt", "xlsx", "pptx"], key=f"upl_biblio_{cat_id}")

                        if st.form_submit_button("🚀 Publicar Recurso en el Curso"):
                            if not tit_act.strip():
                                st.error("Completá el título de la actividad.")
                            else:
                                tipo_db = "Bibliografía" if "Bibliografía" in tipo_modulo else ("Foro" if "Foro" in tipo_modulo else ("Cuestionario" if "Examen" in tipo_modulo else "Tarea"))
                                json_str = json.dumps(preguntas_generadas, ensure_ascii=False) if tipo_db == "Cuestionario" else None
                                
                                ruta_final_biblio = enlace_url
                                if archivo_subido_biblio is not None:
                                    ruta_final_biblio = os.path.join(CARPETA_BIBLIO, f"{cat_id}_{int(time.time())}_{archivo_subido_biblio.name}")
                                    with open(ruta_final_biblio, "wb") as fb:
                                        fb.write(archivo_subido_biblio.getbuffer())

                                c.execute("""
                                    INSERT INTO actividades (catedra_id, seccion_id, titulo, tipo, fecha_limite, duracion_minutos, preguntas_json, descripcion, enlace_archivo, es_obligatorio)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (cat_id, sec_map[sec_elegida], tit_act.strip(), tipo_db, str(f_lim), dur_min, json_str, desc_act, ruta_final_biblio, es_obligatorio_val))
                                conn.commit()
                                st.success("¡Publicado exitosamente!")
                                st.rerun()

            df_secciones = pd.read_sql("SELECT id, titulo, orden FROM secciones WHERE catedra_id = ? ORDER BY orden ASC", conn, params=(cat_id,))
            for _, sec in df_secciones.iterrows():
                st.divider()
                col_s_tit, col_s_del_sec = st.columns([5, 1])
                col_s_tit.markdown(f"### 📂 **{sec['titulo']}**")
                if col_s_del_sec.button("🗑️ Borrar Unidad", key=f"del_sec_{sec['id']}"):
                    c.execute("DELETE FROM actividades WHERE seccion_id = ?", (sec['id'],))
                    c.execute("DELETE FROM secciones WHERE id = ?", (sec['id'],))
                    conn.commit()
                    st.rerun()

                acts = pd.read_sql("SELECT * FROM actividades WHERE seccion_id = ?", conn, params=(sec['id'],))
                for _, a in acts.iterrows():
                    col_act_view, col_act_mod, col_act_del = st.columns([3, 1, 1])
                    with col_act_view:
                        with st.expander(f"{a['tipo']}: {a['titulo']} — Vence: {a['fecha_limite']}"):
                            st.write(a['descripcion'])
                            if a['enlace_archivo']:
                                if os.path.exists(str(a['enlace_archivo'])):
                                    nom_bf = os.path.basename(str(a['enlace_archivo']))
                                    with open(a['enlace_archivo'], "rb") as fb_d:
                                        st.download_button(label=f"📥 Descargar Archivo Bibliográfico ({nom_bf})", data=fb_d.read(), file_name=nom_bf, key=f"dl_bib_{a['id']}")
                                else:
                                    renderizar_recurso_multimedia(a['enlace_archivo'])

                            if a['tipo'] == "Cuestionario" and a['preguntas_json']:
                                with st.popover("👀 Vista Previa"):
                                    st.markdown(f"#### ⏱️ Examen: {a['titulo']}")
                                    try:
                                        pregs_prev = json.loads(a['preguntas_json'])
                                        for p_idx, p_val in enumerate(pregs_prev):
                                            st.markdown(f"**Pregunta N° {p_idx+1}:** {p_val.get('enunciado','')}")
                                            if p_val.get('tipo') in ['multiple_choice', 'verdadero_falso']:
                                                for elec in p_val.get('opciones_config', []):
                                                    st.write(f"○ {elec['texto']}")
                                            st.divider()
                                    except Exception:
                                        st.warning("No se pudo cargar la vista previa.")

                    with col_act_mod:
                        with st.popover("✏️ Modificar"):
                            with st.form(f"form_mod_act_{a['id']}"):
                                nuevo_tit = st.text_input("Título", value=a['titulo'])
                                nueva_desc = st.text_area("Descripción", value=a['descripcion'] if a['descripcion'] else "")
                                nuevo_json = a['preguntas_json']
                                if a['tipo'] == "Cuestionario":
                                    st.markdown("**Estructura de Preguntas (JSON):**")
                                    nuevo_json = st.text_area("Editar JSON de preguntas", value=a['preguntas_json'] if a['preguntas_json'] else "[]", height=150)

                                if st.form_submit_button("Guardar Cambios"):
                                    c.execute("UPDATE actividades SET titulo = ?, descripcion = ?, preguntas_json = ? WHERE id = ?", (nuevo_tit.strip(), nueva_desc, nuevo_json, a['id']))
                                    conn.commit()
                                    st.success("Modificado con éxito.")
                                    st.rerun()

                    with col_act_del:
                        if st.button("🗑️ Borrar", key=f"del_act_{a['id']}"):
                            c.execute("DELETE FROM foro_mensajes WHERE actividad_id = ?", (a['id'],))
                            c.execute("DELETE FROM entregas WHERE actividad_id = ?", (a['id'],))
                            c.execute("DELETE FROM actividades WHERE id = ?", (a['id'],))
                            conn.commit()
                            st.success("Eliminado.")
                            st.rerun()

        # --- 2. PESTAÑA CORRECCIÓN DE TRABAJOS ---
        with tab_correccion:
            st.markdown("### 📥 **Corrección de Trabajos y Entregas de Alumnos**")
            st.caption("Revisá las entregas de los estudiantes, visualizá los porcentajes automáticos de autoría y volcá las calificaciones a la planilla central.")
            
            entregas_db = pd.read_sql("""
                SELECT e.id as entrega_id, u.nombre as alumno, u.email, a.titulo as actividad_titulo, a.tipo as tipo_actividad, a.preguntas_json,
                       e.respuesta_data, e.archivo_ruta, e.nota, e.devolucion, e.tiempo_empleado_seg, e.fecha_entrega, e.reescritura_autorizada
                FROM entregas e
                JOIN actividades a ON e.actividad_id = a.id
                JOIN usuarios u ON e.estudiante_id = u.id
                WHERE a.catedra_id = ?
            """, conn, params=(cat_id,))

            if entregas_db.empty:
                st.info("Aún no hay trabajos ni entregas registradas por los alumnos en este curso.")
            else:
                for _, ent in entregas_db.iterrows():
                    t_min = f" | ⏱️ Tiempo: {round(ent['tiempo_empleado_seg']/60, 1)} min" if ent['tiempo_empleado_seg'] else ""
                    aut_badge = " [🔓 Reescritura Autorizada]" if ent['reescritura_autorizada'] == 1 else ""
                    nota_txt = f"Nota: {ent['nota']}" if ent['nota'] is not None else "Sin calificar"
                    
                    with st.expander(f"📌 {ent['alumno']} — Actividad: {ent['actividad_titulo']} ({ent['tipo_actividad']}){aut_badge} | {nota_txt}{t_min}"):
                        st.caption(f"📅 **Fecha de Entrega:** {ent['fecha_entrega']}")
                        
                        if ent['preguntas_json'] and ent['respuesta_data']:
                            st.markdown("#### **Desglose de Respuestas del Examen:**")
                            try:
                                preguntas = json.loads(ent['preguntas_json'])
                                rtas_al = json.loads(ent['respuesta_data'])
                                
                                for idx, preg in enumerate(preguntas):
                                    num_p = idx + 1
                                    st.markdown(f"**Pregunta N° {num_p}:** {preg.get('enunciado','')}")
                                    st.write(f"Respuesta del alumno: `{rtas_al.get(str(idx), 'Sin responder')}`")
                            except Exception:
                                st.write(f"Datos: {ent['respuesta_data']}")
                        else:
                            texto_alumno = ent['respuesta_data'] if ent['respuesta_data'] else ""
                            if texto_alumno:
                                st.markdown(f"<div class='task-response-box'><b>📝 Texto enviado:</b><br>{texto_alumno}</div>", unsafe_allow_html=True)

                            texto_archivo_extraido = ""
                            if ent['archivo_ruta'] and isinstance(ent['archivo_ruta'], str) and os.path.exists(ent['archivo_ruta']):
                                nombre_archivo_real = os.path.basename(ent['archivo_ruta'])
                                texto_archivo_extraido = extraer_texto_archivo_entrega(ent['archivo_ruta'])
                                with open(ent['archivo_ruta'], "rb") as f_adj:
                                    st.download_button(
                                        label=f"📥 Descargar Archivo Adjunto ({nombre_archivo_real})",
                                        data=f_adj.read(),
                                        file_name=nombre_archivo_real,
                                        key=f"dl_corr_{ent['entrega_id']}"
                                    )

                            texto_a_auditar = texto_alumno if texto_alumno else texto_archivo_extraido
                            if not texto_a_auditar and ent['archivo_ruta']:
                                texto_a_auditar = os.path.basename(str(ent['archivo_ruta']))

                            api_key_auditoria = get_config("gemini_api_key", "")
                            reporte = analizar_antifraude_ia(texto_a_auditar, api_key_auditoria)

                            st.markdown(f"""
                            <div class='ai-detector-box' style='border-left: 5px solid {reporte['color']};'>
                                <h5 style='margin:0 0 6px 0; color:#1e293b;'>📊 Auditoría de Autenticidad y Similitud Académica</h5>
                                • <b>Probabilidad de Contenido asistido:</b> <span style='color:{reporte['color']}; font-weight:bold; font-size:15px;'>{reporte['pct_ia']}%</span><br>
                                • <b>Índice de Similitud con Fuentes Web:</b> <b>{reporte['pct_web']}%</b><br>
                                • <b>Dictamen:</b> {reporte['dictamen']}
                            </div>
                            """, unsafe_allow_html=True)

                        col_aut1, col_aut2 = st.columns([2, 2])
                        with col_aut1:
                            estado_aut = ent['reescritura_autorizada'] == 1
                            if st.button("🔓 Autorizar nuevo envío / reescritura" if not estado_aut else "🔒 Revocar autorización", key=f"btn_aut_corr_{ent['entrega_id']}"):
                                nuevo_estado = 0 if estado_aut else 1
                                c.execute("UPDATE entregas SET reescritura_autorizada = ? WHERE id = ?", (nuevo_estado, ent['entrega_id']))
                                conn.commit()
                                st.success("Estado actualizado.")
                                st.rerun()

                        with st.form(f"form_corr_tab_{ent['entrega_id']}"):
                            n_nueva = st.number_input("Calificación Final (0 a 10)", min_value=0.0, max_value=10.0, value=float(ent['nota']) if ent['nota'] is not None else 7.0)
                            dev_nueva = st.text_area("Devolución Pedagógica para el Alumno", value=ent['devolucion'] if ent['devolucion'] else "")
                            if st.form_submit_button("💾 Guardar y Volcar a Calificaciones"):
                                c.execute("UPDATE entregas SET nota = ?, devolucion = ? WHERE id = ?", (n_nueva, dev_nueva, ent['entrega_id']))
                                conn.commit()
                                st.success("¡Calificación guardada y volcada a la planilla central con éxito!")
                                st.rerun()

        # --- 3. PESTAÑA PARTICIPANTES (MATRICULACIÓN SIMPLIFICADA Y LISTADO ABAJO) ---
        with tab_participantes:
            st.markdown("### **👥 Gestión de Participantes y Alumnos**")
            st.caption("Matriculá nuevos alumnos ingresando únicamente su nombre, apellido, usuario y contraseña.")
            
            with st.form(f"form_alta_alumno_simple_{cat_id}", clear_on_submit=True):
                st.markdown("##### ➕ Matricular Nuevo Alumno")
                col_ma1, col_ma2 = st.columns(2)
                with col_ma1:
                    nom_a = st.text_input("Nombre y Apellido del Alumno *", key=f"nom_a_{cat_id}")
                    usr_a = st.text_input("Usuario de Acceso *", key=f"usr_a_{cat_id}")
                with col_ma2:
                    pwd_a = st.text_input("Contraseña Asignada *", value="1234", key=f"pwd_a_{cat_id}")
                
                if st.form_submit_button("Matricular Alumno"):
                    if nom_a.strip() and usr_a.strip() and pwd_a.strip():
                        try:
                            mail_gen = f"{usr_a.strip()}_{int(time.time())}@campus.edu"
                            c.execute("INSERT INTO usuarios (username, password, nombre, email, rol) VALUES (?, ?, ?, ?, 'estudiante')", (usr_a.strip(), pwd_a.strip(), nom_a.strip(), mail_gen))
                            nuevo_u_id = c.lastrowid
                            c.execute("INSERT INTO matriculas (catedra_id, estudiante_id) VALUES (?, ?)", (cat_id, nuevo_u_id))
                            conn.commit()
                            st.success(f"¡Alumno {nom_a} matriculado con éxito!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("El nombre de usuario ya existe en el sistema.")
                    else:
                        st.error("Por favor complete los campos obligatorios.")

            st.divider()
            st.markdown("### 📋 **Listado General de Alumnos Matriculados**")
            df_matriculados = pd.read_sql("""
                SELECT u.id as user_id, u.nombre, u.username, u.password
                FROM matriculas m 
                JOIN usuarios u ON m.estudiante_id = u.id 
                WHERE m.catedra_id = ?
                ORDER BY u.nombre ASC
            """, conn, params=(cat_id,))

            if df_matriculados.empty:
                st.info("No hay alumnos matriculados en esta cátedra.")
            else:
                for _, al_row in df_matriculados.iterrows():
                    col_p1, col_p2 = st.columns([5, 1])
                    col_p1.markdown(f"👤 **{al_row['nombre']}** &nbsp;|&nbsp; 🔑 Usuario: `{al_row['username']}` &nbsp;|&nbsp; 🔒 Contraseña: `{al_row['password']}`")
                    with col_p2:
                        if st.button("🗑️ Dar de Baja", key=f"del_mat_{al_row['user_id']}_{cat_id}"):
                            c.execute("DELETE FROM matriculas WHERE catedra_id = ? AND estudiante_id = ?", (cat_id, al_row['user_id']))
                            conn.commit()
                            st.success("Alumno dado de baja.")
                            st.rerun()

        # --- 4. PESTAÑA CALIFICACIONES ---
        with tab_calificaciones:
            st.markdown("### 📋 **Planilla Central de Calificaciones**")
            
            alumnos_curso = pd.read_sql("SELECT u.id, u.nombre FROM matriculas m JOIN usuarios u ON m.estudiante_id = u.id WHERE m.catedra_id = ?", conn, params=(cat_id,))
            
            if alumnos_curso.empty:
                st.info("No hay alumnos matriculados en esta cátedra.")
            else:
                acts_eval = pd.read_sql("SELECT id, titulo FROM actividades WHERE catedra_id = ? AND tipo IN ('Tarea', 'Cuestionario')", conn, params=(cat_id,))
                
                tabla_calif_central = []
                for _, al in alumnos_curso.iterrows():
                    fila = {"Estudiante": al['nombre']}
                    
                    notas_parciales = []
                    for _, act in acts_eval.iterrows():
                        res_nt = c.execute("SELECT nota FROM entregas WHERE actividad_id = ? AND estudiante_id = ?", (act['id'], al['id'])).fetchone()
                        if res_nt and res_nt[0] is not None:
                            fila[act['titulo']] = f"{res_nt[0]:.2f}"
                            notas_parciales.append(res_nt[0])
                        else:
                            fila[act['titulo']] = "-"
                    
                    fila["Promedio Trabajos"] = f"{(sum(notas_parciales)/len(notas_parciales)):.2f}" if notas_parciales else "-"

                    per = c.execute("SELECT informe_avance_1, cuatrimestre_1, informe_avance_2, cuatrimestre_2, calificacion_final_dic FROM calificaciones_periodos WHERE catedra_id = ? AND estudiante_id = ?", (cat_id, al['id'])).fetchone()
                    fila["1° Inf"] = per[0] if per else "-"
                    fila["1° Cuat"] = f"{per[1]:.2f}" if per and per[1] is not None else "-"
                    fila["2° Inf"] = per[2] if per else "-"
                    fila["2° Cuat"] = f"{per[3]:.2f}" if per and per[3] is not None else "-"
                    fila["Final Dic"] = f"{per[4]:.2f}" if per and per[4] is not None else "-"

                    tabla_calif_central.append(fila)

                st.dataframe(pd.DataFrame(tabla_calif_central), use_container_width=True, hide_index=True)

                with st.expander("📝 Cargar / Modificar Informes Oficiales (TEA, TEP, TED)"):
                    map_al_cal = {r['nombre']: r['id'] for _, r in alumnos_curso.iterrows()}
                    sel_al_cal = st.selectbox("Alumno:", list(map_al_cal.keys()), key=f"sel_al_cal_{cat_id}")
                    al_cal_id = map_al_cal[sel_al_cal]
                    with st.form(f"form_per_{al_cal_id}_{cat_id}"):
                        n_inf1 = st.selectbox("1° Informe:", ["-", "TEA", "TEP", "TED"], key=f"inf1_{cat_id}")
                        n_c1 = st.number_input("Nota 1° Cuatrimestre:", 0.0, 10.0, 7.0, key=f"c1_{cat_id}")
                        n_inf2 = st.selectbox("2° Informe:", ["-", "TEA", "TEP", "TED"], key=f"inf2_{cat_id}")
                        n_c2 = st.number_input("Nota 2° Cuatrimestre:", 0.0, 10.0, 7.0, key=f"c2_{cat_id}")
                        n_fin = st.number_input("Nota Final Diciembre:", 0.0, 10.0, 7.0, key=f"fin_{cat_id}")
                        if st.form_submit_button("Guardar"):
                            c.execute("""
                                INSERT INTO calificaciones_periodos (catedra_id, estudiante_id, informe_avance_1, cuatrimestre_1, informe_avance_2, cuatrimestre_2, calificacion_final_dic)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(catedra_id, estudiante_id) DO UPDATE SET informe_avance_1=excluded.informe_avance_1, cuatrimestre_1=excluded.cuatrimestre_1, informe_avance_2=excluded.informe_avance_2, cuatrimestre_2=excluded.cuatrimestre_2, calificacion_final_dic=excluded.calificacion_final_dic
                            """, (cat_id, al_cal_id, n_inf1, n_c1, n_inf2, n_c2, n_fin))
                            conn.commit()
                            st.success("Guardado.")
                            st.rerun()

        # --- 5. PESTAÑA ASISTENCIA ---
        with tab_asistencia:
            st.markdown("### **Asistencia**")
            alumnos_asist = pd.read_sql("SELECT u.id, u.nombre FROM matriculas m JOIN usuarios u ON m.estudiante_id = u.id WHERE m.catedra_id = ?", conn, params=(cat_id,))
            if not alumnos_asist.empty:
                fecha_sel = st.date_input("Fecha:", value=date.today(), key=f"date_asist_{cat_id}")
                with st.form(f"form_asist_{cat_id}"):
                    est_dict = {}
                    for _, al in alumnos_asist.iterrows():
                        est_dict[al['id']] = st.radio(al['nombre'], ["Presente", "Ausente"], horizontal=True, key=f"as_{al['id']}_{cat_id}")
                    if st.form_submit_button("Guardar Asistencia"):
                        for aid, estado in est_dict.items():
                            c.execute("INSERT INTO asistencias (catedra_id, estudiante_id, fecha, estado) VALUES (?, ?, ?, ?) ON CONFLICT(catedra_id, estudiante_id, fecha) DO UPDATE SET estado = excluded.estado", (cat_id, aid, str(fecha_sel), estado))
                        conn.commit()
                        st.success("Asistencia guardada.")

                st.divider()
                st.markdown("### 📊 **Resumen de Asistencia General**")
                resumen_asist = []
                for _, al in alumnos_asist.iterrows():
                    total_clases = c.execute("SELECT COUNT(*) FROM asistencias WHERE catedra_id = ? AND estudiante_id = ?", (cat_id, al['id'])).fetchone()[0]
                    total_presentes = c.execute("SELECT COUNT(*) FROM asistencias WHERE catedra_id = ? AND estudiante_id = ? AND estado = 'Presente'", (cat_id, al['id'])).fetchone()[0]
                    total_ausentes = total_clases - total_presentes
                    pct = round((total_presentes / total_clases) * 100, 1) if total_clases > 0 else 0.0
                    resumen_asist.append({"Estudiante": al['nombre'], "Clases": total_clases, "Presentes": total_presentes, "Ausentes": total_ausentes, "% Asistencia": f"{pct}%"})
                st.dataframe(pd.DataFrame(resumen_asist), use_container_width=True, hide_index=True)

        # --- 6. PESTAÑA MENSAJES ---
        with tab_mensajes:
            st.markdown("### ✉️ **Buzón de Mensajes Privados**")
            alumnos_curso = pd.read_sql("SELECT u.id, u.nombre FROM matriculas m JOIN usuarios u ON m.estudiante_id = u.id WHERE m.catedra_id = ?", conn, params=(cat_id,))
            if not alumnos_curso.empty:
                map_al_msg = {r['nombre']: r['id'] for _, r in alumnos_curso.iterrows()}
                sel_al_chat = st.selectbox("Alumno:", list(map_al_msg.keys()), key=f"sel_chat_al_{cat_id}")
                al_chat_id = map_al_msg[sel_al_chat]

                mensajes_priv = pd.read_sql("SELECT m.mensaje, m.fecha, m.emisor_id FROM mensajes_privados m WHERE m.catedra_id = ? AND ((m.emisor_id = ? AND m.receptor_id = ?) OR (m.emisor_id = ? AND m.receptor_id = ?)) ORDER BY m.id ASC", conn, params=(cat_id, u["id"], al_chat_id, al_chat_id, u["id"]))
                for _, msg_p in mensajes_priv.iterrows():
                    st.write(f"{'Yo' if msg_p['emisor_id'] == u['id'] else 'Alumno'}: {msg_p['mensaje']}")

                with st.form(f"form_chat_profe_{cat_id}", clear_on_submit=True):
                    txt_m = st.text_area("Mensaje:", key=f"txt_msg_profe_{cat_id}")
                    if st.form_submit_button("Enviar") and txt_m.strip():
                        c.execute("INSERT INTO mensajes_privados (emisor_id, receptor_id, catedra_id, mensaje, fecha, leido) VALUES (?, ?, ?, ?, ?, 0)", (u["id"], al_chat_id, cat_id, txt_m.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        st.rerun()

# ==============================================================================
# 🎓 VISTA ESTUDIANTE
# ==============================================================================
else:
    st.markdown("## **Mis Cursos**")
    df_mis_cursos = pd.read_sql("SELECT c.id, c.nombre, c.curso_anio, c.escuela, c.profesor_id, u.nombre as profesor_nombre FROM catedras c JOIN matriculas m ON c.id = m.catedra_id JOIN usuarios u ON c.profesor_id = u.id WHERE m.estudiante_id = ?", conn, params=(u["id"],))
    if df_mis_cursos.empty:
        st.warning("No estás matriculado en ninguna materia.")
        st.stop()

    mat_map = {f"{r['nombre']} ({r['curso_anio']})": r for _, r in df_mis_cursos.iterrows()}
    sel_mat_al = st.selectbox("Curso:", list(mat_map.keys()))
    materia_row = mat_map[sel_mat_al]
    materia_id = materia_row["id"]

    tab_al_curso, tab_al_notas, tab_al_asist, tab_al_chat = st.tabs(["📘 Curso", "📊 Calificaciones", "📋 Asistencia", "✉️ Mensajes"])

    with tab_al_curso:
        df_sec_al = pd.read_sql("SELECT id, titulo FROM secciones WHERE catedra_id = ? ORDER BY orden ASC", conn, params=(materia_id,))
        for _, s in df_sec_al.iterrows():
            st.markdown(f"#### 📂 {s['titulo']}")
            acts_al = pd.read_sql("SELECT * FROM actividades WHERE seccion_id = ?", conn, params=(s['id'],))
            for _, act in acts_al.iterrows():
                with st.expander(f"{act['tipo']}: {act['titulo']}"):
                    st.write(act['descripcion'])
                    if act['enlace_archivo']:
                        if os.path.exists(str(act['enlace_archivo'])):
                            nom_bf = os.path.basename(str(act['enlace_archivo']))
                            with open(act['enlace_archivo'], "rb") as f_db:
                                st.download_button(label=f"📥 Descargar Archivo Bibliográfico ({nom_bf})", data=f_db.read(), file_name=nom_bf, key=f"dl_al_bib_{act['id']}")
                        else:
                            renderizar_recurso_multimedia(act['enlace_archivo'])

                    # SI ES TAREA: PERMITE SUBIR PDF O CONTESTAR EN CAMPO DE ESCRITURA
                    if act['tipo'] == "Tarea":
                        ent_al = pd.read_sql("SELECT * FROM entregas WHERE actividad_id = ? AND estudiante_id = ?", conn, params=(act['id'], u['id']))
                        ya_rendido = not ent_al.empty
                        reescritura_permitida = False
                        if ya_rendido:
                            reescritura_permitida = ent_al.iloc[0]['reescritura_autorizada'] == 1

                        if ya_rendido and not reescritura_permitida:
                            data_e = ent_al.iloc[0]
                            st.success(f"Tarea entregada el {data_e['fecha_entrega']}.")
                            if data_e['archivo_ruta'] and os.path.exists(str(data_e['archivo_ruta'])):
                                nom_ent = os.path.basename(str(data_e['archivo_ruta']))
                                with open(data_e['archivo_ruta'], "rb") as fe_d:
                                    st.download_button(label=f"📥 Descargar mi entrega ({nom_ent})", data=fe_d.read(), file_name=nom_ent, key=f"dl_ent_{data_e['id']}")
                            elif data_e['respuesta_data']:
                                st.markdown(f"**Tu respuesta escrita:** {data_e['respuesta_data']}")

                            if data_e['nota'] is not None:
                                st.metric("Calificación:", f"{data_e['nota']}/10")
                                st.info(f"**Devolución del Docente:**\n{data_e['devolucion']}")
                            
                            st.divider()
                            if st.button("🔄 Solicitar Autorización de Reenvío", key=f"req_reenv_tarea_{act['id']}"):
                                msg_auto = f"Hola profesor, solicito autorización para volver a enviar mi tarea en la actividad: '{act['titulo']}'."
                                c.execute("INSERT INTO mensajes_privados (emisor_id, receptor_id, catedra_id, mensaje, fecha, leido) VALUES (?, ?, ?, ?, ?, 0)", (u["id"], materia_row["profesor_id"], materia_id, msg_auto, datetime.now().strftime("%Y-%m-%d %H:%M")))
                                conn.commit()
                                st.success("¡Solicitud enviada al profesor!")
                        else:
                            if reescritura_permitida:
                                st.warning("🔓 El profesor te autorizó a realizar una nueva entrega.")

                            with st.form(f"form_tarea_dual_{act['id']}"):
                                st.markdown("##### ✍️ Responder en campo de texto:")
                                rta_texto = st.text_area("Escribí tu respuesta o desarrollo aquí:")
                                
                                st.markdown("##### 📂 O adjuntar archivo PDF / Word:")
                                arch_pdf = st.file_uploader("Seleccionar archivo:", type=["pdf", "docx", "txt", "zip"], key=f"up_pdf_{act['id']}")

                                if st.form_submit_button("🚀 Enviar Tarea"):
                                    if not rta_texto.strip() and arch_pdf is None:
                                        st.error("Debes escribir una respuesta en texto o adjuntar un archivo.")
                                    else:
                                        r_path = None
                                        if arch_pdf is not None:
                                            r_path = os.path.join(CARPETA_ENTREGAS, f"{u['id']}_{act['id']}_{arch_pdf.name}")
                                            with open(r_path, "wb") as f_up:
                                                f_up.write(arch_pdf.getbuffer())

                                        c.execute("""
                                            INSERT INTO entregas (actividad_id, estudiante_id, fecha_entrega, respuesta_data, archivo_ruta, reescritura_autorizada)
                                            VALUES (?, ?, ?, ?, ?, 0)
                                            ON CONFLICT(actividad_id, estudiante_id) DO UPDATE SET fecha_entrega=excluded.fecha_entrega, respuesta_data=excluded.respuesta_data, archivo_ruta=excluded.archivo_ruta, reescritura_autorizada=0
                                        """, (act['id'], u['id'], datetime.now().strftime("%Y-%m-%d %H:%M"), rta_texto.strip(), r_path))
                                        conn.commit()
                                        st.success("¡Tarea enviada correctamente!")
                                        st.rerun()

                    # SI ES EXAMEN / CUESTIONARIO CON CALIFICACIÓN ESTILO MOODLE
                    elif act['tipo'] == "Cuestionario":
                        ent_al = pd.read_sql("SELECT * FROM entregas WHERE actividad_id = ? AND estudiante_id = ?", conn, params=(act['id'], u['id']))
                        ya_rendido = not ent_al.empty

                        if ya_rendido:
                            data_e = ent_al.iloc[0]
                            st.success(f"Examen entregado. Nota obtenida: {data_e['nota']}/10")
                        else:
                            if st.session_state.examen_en_curso != act['id']:
                                if st.button(f"🚀 Comenzar Examen (Tenés {act['duracion_minutos']} minutos)", key=f"start_ex_{act['id']}"):
                                    st.session_state.examen_en_curso = act['id']
                                    st.session_state.tiempo_inicio_examen = time.time()
                                    st.rerun()

                            if st.session_state.examen_en_curso == act['id']:
                                st.markdown("<div class='antifraude-warn'>⚠️ ATENCIÓN: Si salís de la página o cambiás de pestaña durante el examen, el intento será finalizado y revisado por el docente.</div>", unsafe_allow_html=True)

                                t_pasado = int(time.time() - st.session_state.tiempo_inicio_examen)
                                t_total = act['duracion_minutos'] * 60
                                t_restante = max(0, t_total - t_pasado)
                                
                                mins, segs = divmod(t_restante, 60)
                                st.markdown(f"<div class='timer-box'>⏳ Tiempo Restante: {mins:02d}:{segs:02d}</div>", unsafe_allow_html=True)
                                
                                if t_restante == 0:
                                    st.error("¡El tiempo ha expirado! El examen se cerró automáticamente.")
                                    time.sleep(2)
                                    st.session_state.examen_en_curso = None
                                    st.rerun()

                                pregs = json.loads(act['preguntas_json']) if act['preguntas_json'] else []
                                rtas_seleccionadas = {}
                                
                                with st.form(f"form_rendir_examen_{act['id']}"):
                                    for idx, p in enumerate(pregs):
                                        num_p = idx + 1
                                        t_p = p.get("tipo", "multiple_choice")
                                        
                                        st.markdown(f"**Pregunta N° {num_p}**")
                                        
                                        if t_p in ["multiple_choice", "verdadero_falso"]:
                                            st.markdown(f"*{p['enunciado']}*")
                                            opciones_disp = [elec['texto'] for elec in p.get('opciones_config', [])]
                                            rtas_seleccionadas[idx] = st.radio("Seleccioná la respuesta:", opciones_disp, key=f"ans_{act['id']}_{idx}")
                                        elif t_p == "completar_espacios":
                                            st.markdown(f"*{p['enunciado']}*")
                                            correctas = p['palabras_correctas']
                                            banco_palabras = list(set(correctas + p.get('distractores', [])))
                                            resp_gaps = {}
                                            cols_gaps = st.columns(len(correctas))
                                            for g_idx, cor in enumerate(correctas):
                                                with cols_gaps[g_idx]:
                                                    resp_gaps[f"gap_{g_idx}"] = st.selectbox(f"Espacio #{g_idx+1}:", ["(Seleccionar)"] + banco_palabras, key=f"gap_{act['id']}_{idx}_{g_idx}")
                                            rtas_seleccionadas[idx] = resp_gaps

                                    if st.form_submit_button("Terminar y Enviar Examen"):
                                        puntos_totales = 0.0
                                        max_posible = len(pregs) * 100.0

                                        for idx, p in enumerate(pregs):
                                            t_p = p.get("tipo", "multiple_choice")
                                            if t_p in ["multiple_choice", "verdadero_falso"]:
                                                resp_elegida = rtas_seleccionadas.get(idx)
                                                for elec in p.get('opciones_config', []):
                                                    if elec['texto'] == resp_elegida:
                                                        puntos_totales += float(elec.get('calificacion', 0.0))
                                            elif t_p == "completar_espacios":
                                                correctas = p['palabras_correctas']
                                                gaps_al = rtas_seleccionadas.get(idx, {})
                                                aciertos_gaps = sum(1 for g_idx, cor in enumerate(correctas) if gaps_al.get(f"gap_{g_idx}") == cor)
                                                if correctas:
                                                    puntos_totales += 100.0 * (aciertos_gaps / len(correctas))

                                        nota_calc = round((puntos_totales / max_posible) * 10, 2) if max_posible > 0 else 0.0
                                        nota_calc = min(10.0, max(0.0, nota_calc))
                                        dev_auto = f"Examen finalizado. Calificación obtenida: {nota_calc}/10."

                                        c.execute("""
                                            INSERT INTO entregas (actividad_id, estudiante_id, fecha_entrega, respuesta_data, nota, devolucion, tiempo_empleado_seg, reescritura_autorizada)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                                            ON CONFLICT(actividad_id, estudiante_id) DO UPDATE SET fecha_entrega=excluded.fecha_entrega, respuesta_data=excluded.respuesta_data, nota=excluded.nota, devolucion=excluded.devolucion, tiempo_empleado_seg=excluded.tiempo_empleado_seg, reescritura_autorizada=0
                                        """, (act['id'], u['id'], datetime.now().strftime("%Y-%m-%d %H:%M"), json.dumps(rtas_seleccionadas, ensure_ascii=False), nota_calc, dev_auto, t_pasado))
                                        conn.commit()
                                        st.session_state.examen_en_curso = None
                                        st.session_state.tiempo_inicio_examen = None
                                        st.success(f"Examen enviado correctamente. Nota: {nota_calc}/10")
                                        st.rerun()

    with tab_al_notas:
        st.markdown("### 📊 **Mis Calificaciones y Devoluciones**")
        
        per_al = c.execute("SELECT informe_avance_1, cuatrimestre_1, informe_avance_2, cuatrimestre_2, calificacion_final_dic FROM calificaciones_periodos WHERE catedra_id = ? AND estudiante_id = ?", (materia_id, u['id'])).fetchone()
        if per_al:
            c1, c2, c3 = st.columns(3)
            c1.metric("1° Cuatrimestre", f"{per_al[1]:.2f}" if per_al[1] is not None else "-")
            c2.metric("2° Cuatrimestre", f"{per_al[3]:.2f}" if per_al[3] is not None else "-")
            c3.metric("Calificación Final", f"{per_al[4]:.2f}" if per_al[4] is not None else "-")

        st.divider()
        st.markdown("#### 📝 **Desglose de Trabajos y Exámenes Corregidos:**")
        
        df_notas_estudiante = pd.read_sql("""
            SELECT a.titulo as Actividad, a.tipo as Tipo, e.nota as Calificación, e.devolucion as Devolución, e.fecha_entrega as 'Fecha de Entrega'
            FROM actividades a
            JOIN entregas e ON a.id = e.actividad_id
            WHERE a.catedra_id = ? AND e.estudiante_id = ?
        """, conn, params=(materia_id, u['id']))

        if df_notas_estudiante.empty:
            st.info("Aún no tenés calificaciones publicadas en este curso.")
        else:
            st.dataframe(df_notas_estudiante, use_container_width=True, hide_index=True)

    with tab_al_asist:
        st.markdown("### **Asistencia**")
        df_a = pd.read_sql("SELECT fecha, estado FROM asistencias WHERE catedra_id = ? AND estudiante_id = ?", conn, params=(materia_id, u['id']))
        st.dataframe(df_a, use_container_width=True)

    with tab_al_chat:
        st.markdown("### ✉️ **Mensajes al Profesor**")
        mens_al = pd.read_sql("SELECT mensaje, fecha, emisor_id FROM mensajes_privados WHERE catedra_id = ? AND ((emisor_id = ? AND receptor_id = ?) OR (emisor_id = ? AND receptor_id = ?))", conn, params=(materia_id, u["id"], materia_row["profesor_id"], materia_row["profesor_id"], u["id"]))
        for _, m in mens_al.iterrows():
            st.write(f"{'Yo' if m['emisor_id'] == u['id'] else 'Profesor'}: {m['mensaje']}")
        with st.form("form_msg_est", clear_on_submit=True):
            txt_est = st.text_area("Mensaje:")
            if st.form_submit_button("Enviar") and txt_est.strip():
                c.execute("INSERT INTO mensajes_privados (emisor_id, receptor_id, catedra_id, mensaje, fecha, leido) VALUES (?, ?, ?, ?, ?, 0)", (u["id"], materia_row["profesor_id"], materia_id, txt_est.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                st.rerun()
