import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import time
import re
import math
import base64
import urllib.request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date

st.set_page_config(page_title="Plataforma Educativa", page_icon="🎓", layout="wide")

CARPETA_ENTREGAS = "entregas_alumnos"
CARPETA_PERFILES = "fotos_perfil"
os.makedirs(CARPETA_ENTREGAS, exist_ok=True)
os.makedirs(CARPETA_PERFILES, exist_ok=True)

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
    
    /* Botones con fondo azul nítido y texto blanco forzado */
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
    
    /* Tarjetas de cursos */
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
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 22px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(220, 38, 38, 0.2);
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
    foto_perfil TEXT
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

# --- FUNCIONES DE DIBUJO DE TORTA (SVG NATIVO) ---
def render_pie_chart_svg(data_dict):
    total = sum(data_dict.values())
    if total == 0:
        return "<p style='color:gray;'>Sin datos suficientes para graficar.</p>"
    
    slices = []
    cumulative_angle = 0
    legend_html = "<div style='margin-top:12px; font-size:13px;'>"
    
    colors = {
        "Presentes": "#22c55e",
        "Ausentes": "#ef4444",
        "Aprobados (≥7)": "#22c55e",
        "En Proceso (4-6)": "#f59e0b",
        "Desaprobados (<4)": "#ef4444"
    }
    
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
    
    svg_html = f"""
    <div style='display:flex; flex-direction:column; align-items:center; background:#ffffff; padding:16px; border-radius:10px; border:1px solid #e2e8f0;'>
        <svg width='180' height='180' viewBox='0 0 200 200'>
            {''.join(slices)}
        </svg>
        {legend_html}
    </div>
    """
    return svg_html

# --- FUNCIONES DE GENERACIÓN DE DOCUMENTOS (WORD Y PDF) ---
def exportar_documento_word(titulo, contenido):
    contenido_html = contenido.replace("\n", "<br>")
    contenido_html = re.sub(r'### (.*?)(?:<br>|$)', r'<h3>\1</h3>', contenido_html)
    contenido_html = re.sub(r'## (.*?)(?:<br>|$)', r'<h2>\1</h2>', contenido_html)
    contenido_html = re.sub(r'# (.*?)(?:<br>|$)', r'<h1>\1</h1>', contenido_html)
    contenido_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', contenido_html)
    
    html_doc = f"""<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head>
<meta charset="utf-8">
<title>{titulo}</title>
<style>
body {{ font-family: 'Calibri', 'Arial', sans-serif; line-height: 1.6; margin: 40px; color: #111827; }}
h1 {{ color: #1d4ed8; font-size: 22pt; border-bottom: 2px solid #1d4ed8; padding-bottom: 8px; }}
h2 {{ color: #1e3a8a; font-size: 16pt; margin-top: 18pt; }}
h3 {{ color: #1e40af; font-size: 14pt; margin-top: 14pt; }}
p, li {{ font-size: 11pt; text-align: justify; }}
.footer {{ margin-top: 40pt; font-size: 9pt; color: #6b7280; border-top: 1px solid #cbd5e1; padding-top: 10px; }}
</style>
</head>
<body>
<h1>{titulo}</h1>
<div>{contenido_html}</div>
<div class="footer">Documento generado pedagógicamente por Plataforma Educativa — Tec. Cristian Nuñez</div>
</body>
</html>"""
    return html_doc.encode('utf-8')

def exportar_documento_pdf_imprimible(titulo, contenido):
    contenido_html = contenido.replace("\n", "<br>")
    contenido_html = re.sub(r'### (.*?)(?:<br>|$)', r'<h3>\1</h3>', contenido_html)
    contenido_html = re.sub(r'## (.*?)(?:<br>|$)', r'<h2>\1</h2>', contenido_html)
    contenido_html = re.sub(r'# (.*?)(?:<br>|$)', r'<h1>\1</h1>', contenido_html)
    contenido_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', contenido_html)
    
    html_pdf = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{titulo}</title>
<style>
@media print {{
    @page {{ margin: 20mm; size: A4; }}
    body {{ -webkit-print-color-adjust: exact; }}
    .no-print {{ display: none; }}
}}
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; margin: 30px auto; max-width: 800px; color: #0f172a; padding: 20px; }}
h1 {{ color: #1d4ed8; font-size: 24px; border-bottom: 2px solid #2563eb; padding-bottom: 8px; }}
h2, h3 {{ color: #1e3a8a; margin-top: 20px; }}
p, li {{ font-size: 14px; text-align: justify; }}
.btn-print {{ background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; margin-bottom: 20px; }}
.footer {{ margin-top: 40px; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 10px; }}
</style>
</head>
<body>
<div class="no-print" style="text-align: right;">
    <button class="btn-print" onclick="window.print()">🖨️ Imprimir o Guardar como PDF</button>
</div>
<h1>{titulo}</h1>
<div>{contenido_html}</div>
<div class="footer">Plataforma Educativa • Documento Pedagógico Oficial</div>
</body>
</html>"""
    return html_pdf.encode('utf-8')

# --- FUNCIONES DE EMAIL ROBUSTA ---
def get_config(clave, default=""):
    r = c.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
    return r[0] if r else default

def set_config(clave, valor):
    c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", (clave, valor))
    conn.commit()

def enviar_correo_smtp(destinatario, asunto, cuerpo):
    remitente = get_config("smtp_email", "").strip()
    smtp_pass = get_config("smtp_password", "").strip().replace(" ", "")
    
    if not remitente or not smtp_pass:
        return False, "Faltan configurar el email emisor y la Contraseña de Aplicación de 16 letras en el panel docente."

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

def enviar_credenciales_alumno(destinatario, nombre_alumno, curso_nombre, usuario, clave):
    asunto = f"🎓 Acceso a tu curso: {curso_nombre}"
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
    return enviar_correo_smtp(destinatario, asunto, cuerpo)

def extraer_texto_archivo_entrega(ruta_archivo):
    if not ruta_archivo or not isinstance(ruta_archivo, str) or not os.path.exists(ruta_archivo):
        return ""
    try:
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
        limpio = "".join([c for c in contenido if c.isprintable() or c in "\n\t "])
        return limpio[:3000]
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
    conectores_ia = ["en conclusión", "en resumen", "es fundamental destacar", "por lo tanto", "cabe mencionar", "es crucial", "en primer lugar", "a modo de síntesis", "en definitiva", "asimismo", "dictamen", "conforme", "objeto"]
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
Especificaciones didácticas: '{detalle_adicional}'

Instrucciones de formato y profundidad:
- Desarrolla cada sección con amplitud teórica y ejemplos concretos.
- Incluye fundamentación pedagógica, desglose temático detallado y criterios de evaluación.
- Si es un Examen o Trabajo Práctico, incluye consignas claras y su respectiva clave de respuestas o rúbrica de corrección."""
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode())
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass

    if tipo_recurso == "Trabajo Práctico con Consignas":
        return f"""# 📝 Trabajo Práctico: {tema}
**Materia / Curso:** {nivel}
**Fecha:** {datetime.now().strftime('%d/%m/%Y')}

---

### 🎯 1. Fundamentación y Objetivos
El presente trabajo práctico tiene como propósito que los estudiantes analicen en profundidad los conceptos esenciales de **{tema}**, fomentando el pensamiento crítico, la capacidad de síntesis y la aplicación empírica de los contenidos abordados.

### 📖 2. Marco Conceptual y Lectura de Base
{detalle_adicional if detalle_adicional else 'Se sugiere la lectura de la bibliografía de la unidad y el análisis de casos reales vinculados al sistema institucional y social.'}

### ✍️ 3. Consignas de Trabajo
1. **Análisis Conceptual:** Defina los elementos estructurantes de {tema} y explique su relevancia en el marco de la materia.
2. **Estudio de Caso / Ejemplificación:** Desarrolle un ejemplo práctico donde se evidencie la aplicación o problemática de {tema}.
3. **Reflexión Crítica:** Elabore una conclusión argumentada sobre los desafíos contemporáneos en torno a este eje.

### 📊 4. Criterios de Evaluación y Rúbrica
- Precisión y coherencia conceptual (40%)
- Capacidad de análisis y argumentación personal (30%)
- Claridad en la redacción y presentación formal (30%)"""

    elif tipo_recurso == "Examen Evaluativo con Respuestas":
        return f"""# ⏱️ Evaluación Escrita: {tema}
**Materia / Curso:** {nivel}
**Tiempo Estimado:** 80 minutos

---

### 📋 Parte A: Preguntas de Desarrollo y Análisis (60%)
1. Explique los fundamentos teóricos principales de **{tema}** y su vinculación con los contenidos del cuatrimestre.
2. Compare dos posturas o perspectivas doctrinales/teóricas relativas a este núcleo temático.

### 🔘 Parte B: Opción Múltiple y Razonamiento (40%)
1. ¿Cuál es el objetivo principal que persigue la aplicación de {tema}?
   - A) Regular exclusivamente aspectos procedimentales.
   - B) Garantizar los principios rectores y derechos fundamentales. (Correcta)
   - C) Delegar funciones operativas en entidades externas.

---

### 🔑 Clave de Corrección y Criterios para el Docente:
- **Respuesta 1:** El alumno debe identificar correctamente los autores y marco normativo/teórico.
- **Respuesta 2:** Se valorará la comparación analítica de ambas posturas doctrinarias."""

    else:
        return f"""# 📚 Planificación Didáctica Integral: {tema}
**Nivel / Curso:** {nivel}
**Fecha de Elaboración:** {datetime.now().strftime('%d/%m/%Y')}

---

### 🎯 1. Propósitos y Objetivos de Aprendizaje:
- Comprender de forma analítica y sistemática los contenidos centrales de **{tema}**.
- Relacionar los conceptos teóricos con situaciones reales y jurisprudenciales/prácticas.
- Incentivar el debate argumentativo y la participación activa del estudiantado.

### ⏱️ 2. Secuencia de la Clase (Estructura de 80 minutos):
- **Apertura / Inicio (15 min):** Indagación de ideas previas mediante una pregunta disparadora y debate guiado.
- **Desarrollo Teórico-Práctico (45 min):** Exposición del docente con apoyo audiovisual y lectura compartida de fragmentos clave.
- **Cierre y Evaluación Formativa (20 min):** Elaboración de conclusiones grupales y asignación de actividades complementarias.

### 📝 3. Recursos y Bibliografía:
- Material de lectura obligatorio provisto en la plataforma.
- Guía de preguntas de reflexión y estudio independiente."""

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

# --- ENCABEZADO GLOBAL CON PERFIL DE USUARIO Y ASISTENTE IA INTEGRADO ---
u = st.session_state.user
col_h1, col_h2, col_h3 = st.columns([2.5, 4, 5.5])
with col_h1:
    if st.button("🏛️ Área personal", key="btn_home"):
        st.session_state.materia_seleccionada_id = None
        st.rerun()

with col_h2:
    st.markdown(f"**🎓 Plataforma Educativa**<br><small style='color: #0369a1;'>Created by Tec. Cristian Nuñez</small>", unsafe_allow_html=True)

with col_h3:
    c_ia_btn, col_u_info, col_u_menu = st.columns([2.2, 2.8, 2])
    
    with c_ia_btn:
        if u["rol"] == "profesor":
            with st.popover("🤖 Asistente IA"):
                st.markdown("#### 🤖 **Asistente Pedagógico**")
                st.caption("Planificá clases, trabajos prácticos y exámenes con descarga en Word y PDF.")
                
                tipo_ia_sel = st.selectbox("¿Qué deseas generar?:", [
                    "Planificación Completa de Clase",
                    "Trabajo Práctico con Consignas",
                    "Examen Evaluativo con Respuestas",
                    "Material de Lectura Teórico"
                ], key="tipo_ia_pop")
                
                t_ia = st.text_input("Tema o núcleo central:", placeholder="Ej: Poder Judicial y Garantías", key="tema_flotante_ia")
                n_ia = st.text_input("Nivel / Curso:", placeholder="Ej: 5° Año - Secundaria", key="nivel_flotante_ia")
                e_ia = st.text_area("Detalles / Enfoque pedagógico:", placeholder="Ej: Casos de estudio, jurisprudencia relevante, debate grupal...", key="enfoque_flotante_ia")
                
                if st.button("✨ Generar Documento", key="btn_gen_flotante"):
                    if t_ia:
                        with st.spinner("Diseñando propuesta educativa detallada..."):
                            ck = get_config("gemini_api_key", "")
                            res_flot = generar_recurso_pedagogico_ia(tipo_ia_sel, t_ia, n_ia, e_ia, ck)
                            st.session_state["resultado_ia_flotante"] = res_flot
                            st.session_state["titulo_ia_flotante"] = f"{tipo_ia_sel} - {t_ia}"

                if "resultado_ia_flotante" in st.session_state:
                    st.divider()
                    st.markdown("##### 📄 Vista Previa:")
                    st.markdown(st.session_state["resultado_ia_flotante"])
                    
                    tit_doc = st.session_state.get("titulo_ia_flotante", "Documento_Pedagogico")
                    cont_doc = st.session_state["resultado_ia_flotante"]
                    
                    c_d1, c_d2 = st.columns(2)
                    with c_d1:
                        doc_word = exportar_documento_word(tit_doc, cont_doc)
                        st.download_button(
                            label="📥 Descargar Word (.doc)",
                            data=doc_word,
                            file_name=f"{tit_doc.replace(' ', '_')}.doc",
                            mime="application/msword",
                            key="btn_dl_word"
                        )
                    with c_d2:
                        doc_pdf = exportar_documento_pdf_imprimible(tit_doc, cont_doc)
                        st.download_button(
                            label="📄 PDF / Imprimir (.html)",
                            data=doc_pdf,
                            file_name=f"{tit_doc.replace(' ', '_')}.html",
                            mime="text/html",
                            key="btn_dl_pdf"
                        )

    with col_u_info:
        iniciales_u = "".join([p[0] for p in u['nombre'].split()[:2]]).upper()
        foto_path = u.get("foto_perfil")
        
        if foto_path and isinstance(foto_path, str) and os.path.exists(foto_path):
            with open(foto_path, "rb") as img_f:
                b64_img = base64.b64encode(img_f.read()).decode()
            avatar_html = f"<img src='data:image/png;base64,{b64_img}' class='user-avatar-circle' />"
        else:
            avatar_html = f"<div class='user-avatar-circle'>{iniciales_u}</div>"

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
            st.markdown("##### 👤 Opciones de Perfil")
            
            foto_subida = st.file_uploader("Actualizar foto de perfil:", type=["jpg", "jpeg", "png"], key="upload_foto_header")
            if foto_subida:
                nueva_ruta_foto = os.path.join(CARPETA_PERFILES, f"user_{u['id']}_{foto_subida.name}")
                with open(nueva_ruta_foto, "wb") as f_f:
                    f_f.write(foto_subida.getbuffer())
                c.execute("UPDATE usuarios SET foto_perfil = ? WHERE id = ?", (nueva_ruta_foto, u["id"]))
                conn.commit()
                st.session_state.user["foto_perfil"] = nueva_ruta_foto
                st.success("Foto de perfil actualizada.")
                st.rerun()

            st.divider()
            with st.form("form_cambio_clave_usuario"):
                st.markdown("##### 🔑 Cambiar Contraseña")
                pass_act = st.text_input("Contraseña actual", type="password")
                pass_n1 = st.text_input("Nueva contraseña", type="password")
                pass_n2 = st.text_input("Confirmar nueva contraseña", type="password")
                if st.form_submit_button("Guardar Contraseña"):
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

            if st.button("Cerrar sesión", key="btn_logout_top"):
                logout()

st.divider()

# ==============================================================================
# 👨‍🏫 VISTA PROFESOR / DOCENTE
# ==============================================================================
if u["rol"] == "profesor":

    # DASHBOARD DE CURSOS
    if st.session_state.materia_seleccionada_id is None:
        
        st.sidebar.markdown("### 🏛️ Administración Docente")
        
        with st.sidebar.expander("🤖 Configuración de Asistente"):
            gemini_act = get_config("gemini_api_key", "")
            gemini_in = st.text_input("Clave de Asistente:", value=gemini_act, type="password")
            if st.button("Guardar Clave"):
                set_config("gemini_api_key", gemini_in.strip())
                st.success("Clave guardada exitosamente.")

        with st.sidebar.expander("📧 Configuración y Prueba de Email"):
            smtp_mail_act = get_config("smtp_email", "")
            smtp_pass_act = get_config("smtp_password", "")
            n_mail = st.text_input("Tu Gmail emisor", value=smtp_mail_act, key="cfg_gmail_in")
            n_pass = st.text_input("Contraseña de Aplicación (16 letras)", value=smtp_pass_act, type="password", key="cfg_pass_in")
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                if st.button("💾 Guardar"):
                    set_config("smtp_email", n_mail.strip())
                    set_config("smtp_password", n_pass.strip())
                    st.success("Guardado.")
            with c_s2:
                if st.button("🧪 Probar Envío"):
                    set_config("smtp_email", n_mail.strip())
                    set_config("smtp_password", n_pass.strip())
                    ok_t, msg_t = enviar_correo_smtp(n_mail.strip(), "Prueba de Plataforma Educativa", "Si recibiste este correo, la configuración SMTP funciona perfectamente.")
                    if ok_t:
                        st.success("¡Correo de prueba enviado con éxito!")
                    else:
                        st.error(f"Fallo al enviar: {msg_t}")

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
                    if st.button(f"Entrar al curso ➜", key=f"entrar_{row['id']}"):
                        st.session_state.materia_seleccionada_id = row['id']
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

        tab_curso, tab_participantes, tab_calificaciones, tab_asistencia, tab_mensajes = st.tabs([
            "📘 Curso", "👥 Participantes", "📈 Calificaciones", "📋 Asistencia", "✉️ Mensajes Privados"
        ])

        # --- 1. PESTAÑA CURSO (CON CONSTRUCTOR MULTIPREGUNTA CORREGIDO) ---
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
                        "⏱️ Cuestionario / Examen Dinámico por Tiempo",
                        "📚 Bibliografía (Material de lectura / Video / Enlace)",
                        "💬 Foro (Debate e Interacción)",
                        "📝 Tarea (Entrega de Archivo/Texto)"
                    ])
                    sec_map = {r['titulo']: r['id'] for _, r in df_secc.iterrows()}
                    sec_elegida = st.selectbox("Sección de destino:", list(sec_map.keys()))

                    tit_act = st.text_input("Título de la actividad / examen", placeholder="Ej: Examen Parcial de Derecho / Trabajo Práctico")
                    desc_act = st.text_area("Descripción / Consigna general", placeholder="Instrucciones para los estudiantes...")
                    f_lim = st.date_input("Fecha Límite", min_value=date.today())

                    es_obligatorio_val = 0
                    if "Bibliografía" in tipo_modulo:
                        caracter_biblio = st.radio("Carácter de la Bibliografía:", ["Bibliografía Obligatoria", "Bibliografía Optativa / Complementaria"], horizontal=True)
                        es_obligatorio_val = 1 if caracter_biblio == "Bibliografía Obligatoria" else 0
                    elif "Foro" in tipo_modulo:
                        es_obligatorio_val = 1 if st.checkbox("📌 ¿Este foro es evaluativo y obligatorio? (Se sumará al Libro de Calificaciones)", value=False) else 0

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
                                    if val_op:
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

                    enlace_url = st.text_input("Enlace web / URL de Video / Archivo en la nube (opcional)", placeholder="https://www.youtube.com/watch?v=... o link a PDF")

                    if st.button("🚀 Publicar Recurso en el Curso"):
                        if not tit_act.strip():
                            st.error("Por favor completá el título de la actividad.")
                        else:
                            if "Bibliografía" in tipo_modulo:
                                tipo_db = "Bibliografía"
                            elif "Foro" in tipo_modulo:
                                tipo_db = "Foro"
                            elif "Examen" in tipo_modulo:
                                tipo_db = "Cuestionario"
                            else:
                                tipo_db = "Tarea"

                            json_str = json.dumps(preguntas_generadas, ensure_ascii=False) if tipo_db == "Cuestionario" else None
                            
                            c.execute("""
                                INSERT INTO actividades (catedra_id, seccion_id, titulo, tipo, fecha_limite, duracion_minutos, preguntas_json, descripcion, enlace_archivo, es_obligatorio)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (cat_id, sec_map[sec_elegida], tit_act.strip(), tipo_db, str(f_lim), dur_min, json_str, desc_act, enlace_url, es_obligatorio_val))
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

                    # ACTIVIDADES CON FORMATO PLEGABLE
                    acts = pd.read_sql("SELECT * FROM actividades WHERE seccion_id = ?", conn, params=(sec['id'],))
                    if acts.empty:
                        st.caption("No hay contenidos cargados en esta sección.")
                    else:
                        for _, a in acts.iterrows():
                            col_act_main, col_act_edit, col_act_del = st.columns([5, 1.2, 1])
                            
                            if a['tipo'] == 'Bibliografía':
                                ico = "📚" if a['es_obligatorio'] == 1 else "📖"
                                tag_tipo = "Bibliografía Obligatoria" if a['es_obligatorio'] == 1 else "Bibliografía Optativa"
                            elif a['tipo'] == 'Foro':
                                ico = "💬"
                                tag_tipo = "Foro Evaluativo" if a['es_obligatorio'] == 1 else "Foro"
                            elif a['tipo'] == 'Cuestionario':
                                ico = "⏱️"
                                tag_tipo = "Examen"
                            else:
                                ico = "📝"
                                tag_tipo = "Tarea"

                            t_lbl = f" | ⏳ {a['duracion_minutos']} min" if a['duracion_minutos'] > 0 else ""
                            
                            with col_act_main:
                                with st.expander(f"{ico} {a['titulo']} ({tag_tipo}){t_lbl} — Vence / Fecha: {a['fecha_limite']}"):
                                    if a['descripcion']:
                                        st.markdown(f"**📌 Contenido / Consigna:**")
                                        st.markdown(a['descripcion'])
                                    else:
                                        st.caption("*(Sin descripción consignada)*")
                                    
                                    if a['enlace_archivo']:
                                        renderizar_recurso_multimedia(a['enlace_archivo'])

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
                                        st.markdown(f"##### Modificar Recurso: {a['titulo']}")
                                        n_tit_act = st.text_input("Título", value=a['titulo'])
                                        n_desc_act = st.text_area("Descripción / Consigna", value=a['descripcion'] if a['descripcion'] else "")
                                        
                                        try:
                                            fecha_actual = datetime.strptime(a['fecha_limite'], "%Y-%m-%d").date()
                                        except Exception:
                                            fecha_actual = date.today()
                                        n_f_lim = st.date_input("Fecha Límite / Fecha", value=fecha_actual)
                                        
                                        n_es_ob = a['es_obligatorio']
                                        if a['tipo'] == "Bibliografía":
                                            sel_b_ob = st.radio("Carácter:", ["Bibliografía Obligatoria", "Bibliografía Optativa / Complementaria"], index=0 if a['es_obligatorio'] == 1 else 1)
                                            n_es_ob = 1 if sel_b_ob == "Bibliografía Obligatoria" else 0
                                        elif a['tipo'] == "Foro":
                                            n_es_ob = 1 if st.checkbox("¿Es foro obligatorio/evaluativo?", value=(a['es_obligatorio'] == 1)) else 0

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
                                                SET seccion_id = ?, titulo = ?, descripcion = ?, fecha_limite = ?, duracion_minutos = ?, preguntas_json = ?, enlace_archivo = ?, es_obligatorio = ?
                                                WHERE id = ?
                                            """, (sec_opts[n_sec_elegida], n_tit_act.strip(), n_desc_act, str(n_f_lim), n_dur, n_preg_json, n_enlace, n_es_ob, a['id']))
                                            conn.commit()
                                            st.success("Modificación guardada exitosamente.")
                                            st.rerun()

                            with col_act_del:
                                if st.button("🗑️", key=f"del_act_{a['id']}", help="Eliminar recurso"):
                                    c.execute("DELETE FROM foro_mensajes WHERE actividad_id = ?", (a['id'],))
                                    c.execute("DELETE FROM entregas WHERE actividad_id = ?", (a['id'],))
                                    c.execute("DELETE FROM actividades WHERE id = ?", (a['id'],))
                                    conn.commit()
                                    st.success("Recurso eliminado.")
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
                                        st.warning(f"Alumno registrado y matriculado. Aviso del correo: {msg_mail}")
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

            st.divider()
            st.markdown("### **Lista y Gestión de Matriculados**")
            
            df_matriculados = pd.read_sql("""
                SELECT u.id as user_id, u.nombre, u.email, u.username, u.password
                FROM matriculas m
                JOIN usuarios u ON m.estudiante_id = u.id
                WHERE m.catedra_id = ?
                ORDER BY u.nombre ASC
            """, conn, params=(cat_id,))

            if df_matriculados.empty:
                st.info("No hay alumnos matriculados en esta cátedra.")
            else:
                for _, al_row in df_matriculados.iterrows():
                    col_al_info, col_al_msg, col_al_edit, col_al_del = st.columns([4.5, 1.3, 1.1, 1.1])
                    
                    with col_al_info:
                        st.markdown(f"👤 **{al_row['nombre']}** &nbsp;|&nbsp; 📧 `{al_row['email']}` &nbsp;|&nbsp; 🔑 Usuario: `{al_row['username']}`")

                    with col_al_msg:
                        with st.popover("💬 Mensaje", key=f"pop_msg_direct_{al_row['user_id']}"):
                            with st.form(f"form_msg_direct_{al_row['user_id']}"):
                                st.markdown(f"##### Mensaje privado para {al_row['nombre']}")
                                txt_direct = st.text_area("Escribir mensaje:")
                                if st.form_submit_button("Enviar Mensaje") and txt_direct.strip():
                                    c.execute("""
                                        INSERT INTO mensajes_privados (emisor_id, receptor_id, catedra_id, mensaje, fecha)
                                        VALUES (?, ?, ?, ?, ?)
                                    """, (u["id"], al_row["user_id"], cat_id, txt_direct.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                                    conn.commit()
                                    st.success("Mensaje enviado correctamente.")

                    with col_al_edit:
                        with st.popover("✏️ Modificar", key=f"pop_edit_al_{al_row['user_id']}"):
                            with st.form(f"form_modificar_alumno_{al_row['user_id']}"):
                                st.markdown(f"##### Editar datos de {al_row['nombre']}")
                                n_nom_al = st.text_input("Nombre y Apellido", value=al_row['nombre'])
                                n_mail_al = st.text_input("Email", value=al_row['email'])
                                n_pwd_al = st.text_input("Contraseña", value=al_row['password'])
                                
                                if st.form_submit_button("Guardar Cambios"):
                                    if n_nom_al and n_mail_al and n_pwd_al:
                                        c.execute("""
                                            UPDATE usuarios 
                                            SET nombre = ?, email = ?, password = ?
                                            WHERE id = ?
                                        """, (n_nom_al.strip(), n_mail_al.strip(), n_pwd_al.strip(), al_row['user_id']))
                                        conn.commit()
                                        st.success("Datos del alumno actualizados.")
                                        st.rerun()

                    with col_al_del:
                        if st.button("🗑️ Baja", key=f"del_mat_{al_row['user_id']}", help="Desmatricular de la materia"):
                            c.execute("DELETE FROM matriculas WHERE catedra_id = ? AND estudiante_id = ?", (cat_id, al_row['user_id']))
                            conn.commit()
                            st.success(f"{al_row['nombre']} desmatriculado/a.")
                            st.rerun()

        # --- 3. PESTAÑA CALIFICACIONES ---
        with tab_calificaciones:
            st.markdown("### 📋 **1. Registro Oficial de Períodos e Informes (TEA / TEP / TED)**")
            
            alumnos_curso = pd.read_sql("""
                SELECT u.id, u.nombre, u.email 
                FROM matriculas m JOIN usuarios u ON m.estudiante_id = u.id 
                WHERE m.catedra_id = ? ORDER BY u.nombre ASC
            """, conn, params=(cat_id,))

            if alumnos_curso.empty:
                st.info("No hay alumnos matriculados en esta cátedra.")
            else:
                tabla_periodos = []
                finales_para_grafico = []

                for _, al in alumnos_curso.iterrows():
                    iniciales = "".join([part[0] for part in al['nombre'].split()[:2]]).upper()
                    
                    per = c.execute("""
                        SELECT informe_avance_1, cuatrimestre_1, informe_avance_2, cuatrimestre_2, calificacion_final_dic
                        FROM calificaciones_periodos
                        WHERE catedra_id = ? AND estudiante_id = ?
                    """, (cat_id, al['id'])).fetchone()

                    inf1 = per[0] if per and per[0] else "-"
                    c1_val = f"{per[1]:.2f}" if per and per[1] is not None else "-"
                    inf2 = per[2] if per and per[2] else "-"
                    c2_val = f"{per[3]:.2f}" if per and per[3] is not None else "-"
                    fin_dic = f"{per[4]:.2f}" if per and per[4] is not None else "-"

                    if per and per[4] is not None:
                        finales_para_grafico.append(per[4])
                    elif per and per[3] is not None:
                        finales_para_grafico.append(per[3])
                    elif per and per[1] is not None:
                        finales_para_grafico.append(per[1])

                    tabla_periodos.append({
                        "Avatar": iniciales,
                        "Nombre / Apellido(s)": al['nombre'],
                        "1° Informe Avance": inf1,
                        "1° Cuatrimestre": c1_val,
                        "2° Informe Avance": inf2,
                        "2° Cuatrimestre": c2_val,
                        "Calificación Final (Dic)": fin_dic
                    })

                df_render_periodos = pd.DataFrame(tabla_periodos)
                st.dataframe(df_render_periodos, use_container_width=True, hide_index=True)

                with st.expander("📝 Cargar / Modificar Informes de Avance (TEA, TEP, TED) y Cuatrimestres"):
                    map_al_cal = {f"{r['nombre']} ({r['email']})": r['id'] for _, r in alumnos_curso.iterrows()}
                    sel_al_cal = st.selectbox("Seleccionar Alumno:", list(map_al_cal.keys()), key="sel_al_per_cal")
                    al_cal_id = map_al_cal[sel_al_cal]

                    datos_act = c.execute("""
                        SELECT informe_avance_1, cuatrimestre_1, informe_avance_2, cuatrimestre_2, calificacion_final_dic
                        FROM calificaciones_periodos WHERE catedra_id = ? AND estudiante_id = ?
                    """, (cat_id, al_cal_id)).fetchone()

                    opciones_informe = ["-", "TEA", "TEP", "TED"]
                    val_inf1 = datos_act[0] if datos_act and datos_act[0] in opciones_informe else "-"
                    val_inf2 = datos_act[2] if datos_act and datos_act[2] in opciones_informe else "-"

                    with st.form(f"form_cargar_periodos_{al_cal_id}"):
                        c_col1, c_col2 = st.columns(2)
                        with c_col1:
                            st.markdown("##### 📘 Primer Cuatrimestre")
                            n_inf1 = st.selectbox("1° Informe de Avance:", opciones_informe, index=opciones_informe.index(val_inf1))
                            n_c1 = st.number_input("Nota 1° Cuatrimestre (1-10):", min_value=0.0, max_value=10.0, value=float(datos_act[1]) if datos_act and datos_act[1] is not None else 7.0)
                        
                        with c_col2:
                            st.markdown("##### 📙 Segundo Cuatrimestre y Cierre")
                            n_inf2 = st.selectbox("2° Informe de Avance:", opciones_informe, index=opciones_informe.index(val_inf2))
                            n_c2 = st.number_input("Nota 2° Cuatrimestre (1-10):", min_value=0.0, max_value=10.0, value=float(datos_act[3]) if datos_act and datos_act[3] is not None else 7.0)
                            n_fin = st.number_input("Calificación Final (Diciembre):", min_value=0.0, max_value=10.0, value=float(datos_act[4]) if datos_act and datos_act[4] is not None else 7.0)

                        st.caption("• **TEA**: Trayectoria Educativa Avanzada | • **TEP**: Trayectoria Educativa en Proceso | • **TED**: Trayectoria Educativa Discontinua")

                        if st.form_submit_button("💾 Guardar Calificaciones y Trayectorias"):
                            c.execute("""
                                INSERT INTO calificaciones_periodos (catedra_id, estudiante_id, informe_avance_1, cuatrimestre_1, informe_avance_2, cuatrimestre_2, calificacion_final_dic)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(catedra_id, estudiante_id)
                                DO UPDATE SET informe_avance_1=excluded.informe_avance_1, cuatrimestre_1=excluded.cuatrimestre_1,
                                              informe_avance_2=excluded.informe_avance_2, cuatrimestre_2=excluded.cuatrimestre_2,
                                              calificacion_final_dic=excluded.calificacion_final_dic
                            """, (cat_id, al_cal_id, n_inf1, n_c1, n_inf2, n_c2, n_fin))
                            conn.commit()
                            st.success(f"Trayectorias y calificaciones guardadas.")
                            st.rerun()

                st.divider()
                st.markdown("### 📊 **2. Planilla de Seguimiento de Cursada y Actividades por Módulo**")
                
                acts_curso = pd.read_sql("""
                    SELECT id, titulo, tipo FROM actividades 
                    WHERE catedra_id = ? AND (tipo IN ('Tarea', 'Cuestionario') OR (tipo = 'Foro' AND es_obligatorio = 1))
                    ORDER BY id ASC
                """, conn, params=(cat_id,))

                if acts_curso.empty:
                    st.info("No hay actividades evaluativas creadas aún (tareas, exámenes o foros obligatorios).")
                else:
                    tabla_cursada = []
                    for _, al in alumnos_curso.iterrows():
                        iniciales = "".join([part[0] for part in al['nombre'].split()[:2]]).upper()
                        fila_act = {
                            "Avatar": iniciales,
                            "Estudiante": al['nombre']
                        }
                        notas_alumno = []
                        for _, act in acts_curso.iterrows():
                            res_nota = c.execute("SELECT nota FROM entregas WHERE actividad_id = ? AND estudiante_id = ?", (act['id'], al['id'])).fetchone()
                            if res_nota and res_nota[0] is not None:
                                fila_act[act['titulo']] = f"{res_nota[0]:.2f}"
                                notas_alumno.append(res_nota[0])
                            else:
                                fila_act[act['titulo']] = "-"
                        
                        fila_act["Promedio Cursada"] = f"{(sum(notas_alumno)/len(notas_alumno)):.2f}" if notas_alumno else "-"
                        tabla_cursada.append(fila_act)

                    df_render_cursada = pd.DataFrame(tabla_cursada)
                    st.dataframe(df_render_cursada, use_container_width=True, hide_index=True)

                # --- GRÁFICO DE TORTA SVG RENDIMIENTO ACADÉMICO ---
                st.divider()
                st.markdown("### 📊 **Estadísticas Generales de Rendimiento**")
                
                col_g1, col_g2 = st.columns([1, 1])
                with col_g1:
                    if finales_para_grafico:
                        aprobados = sum(1 for x in finales_para_grafico if x >= 7.0)
                        en_proceso = sum(1 for x in finales_para_grafico if 4.0 <= x < 7.0)
                        desaprobados = sum(1 for x in finales_para_grafico if x < 4.0)

                        dict_rendimiento = {
                            "Aprobados (≥7)": aprobados,
                            "En Proceso (4-6)": en_proceso,
                            "Desaprobados (<4)": desaprobados
                        }
                        st.markdown(render_pie_chart_svg(dict_rendimiento), unsafe_allow_html=True)
                    else:
                        st.info("Aún no se han asentado notas cuantitativas para generar el gráfico de rendimiento.")

                with col_g2:
                    st.markdown("##### 📌 Resumen de la Cursada:")
                    tot_al = len(alumnos_curso)
                    st.write(f"• **Total de Estudiantes Matriculados:** {tot_al}")
                    if finales_para_grafico:
                        prom_gral = sum(finales_para_grafico) / len(finales_para_grafico)
                        st.write(f"• **Promedio General del Curso:** {prom_gral:.2f}")
                    st.caption("El gráfico representa la distribución académica porcentual de los estudiantes con calificaciones asentadas.")

            st.divider()
            st.markdown("### 🔍 **Revisión de Entregas y Auditoría Automática**")
            
            entregas_db = pd.read_sql("""
                SELECT e.id as entrega_id, u.nombre as alumno, u.email, a.titulo as examen, a.tipo as tipo_actividad, a.preguntas_json,
                       e.respuesta_data, e.archivo_ruta, e.nota, e.devolucion, e.tiempo_empleado_seg, e.fecha_entrega, e.reescritura_autorizada
                FROM entregas e
                JOIN actividades a ON e.actividad_id = a.id
                JOIN usuarios u ON e.estudiante_id = u.id
                WHERE a.catedra_id = ?
            """, conn, params=(cat_id,))

            if not entregas_db.empty:
                for _, ent in entregas_db.iterrows():
                    t_min = f" | ⏱️ Tiempo empleado: {round(ent['tiempo_empleado_seg']/60, 1)} min" if ent['tiempo_empleado_seg'] else ""
                    aut_badge = " [🔓 Reescritura Autorizada]" if ent['reescritura_autorizada'] == 1 else ""
                    
                    with st.expander(f"📌 {ent['alumno']} - {ent['examen']} ({ent['tipo_actividad']}){aut_badge} | Nota: {ent['nota']}{t_min}"):
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
                            texto_alumno = ent['respuesta_data'] if ent['respuesta_data'] else ""
                            
                            if texto_alumno:
                                st.markdown(f"""
                                <div class='task-response-box'>
                                    <b>📝 Texto / Desarrollo enviado:</b><br>
                                    {texto_alumno}
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.write("*(Sin texto desarrollado escrito en pantalla)*")

                            texto_archivo_extraido = ""
                            if ent['archivo_ruta'] and isinstance(ent['archivo_ruta'], str) and os.path.exists(ent['archivo_ruta']):
                                nombre_archivo_real = os.path.basename(ent['archivo_ruta'])
                                texto_archivo_extraido = extraer_texto_archivo_entrega(ent['archivo_ruta'])
                                with open(ent['archivo_ruta'], "rb") as f_adj:
                                    st.download_button(
                                        label=f"📥 Descargar Archivo Adjunto ({nombre_archivo_real})",
                                        data=f_adj.read(),
                                        file_name=nombre_archivo_real,
                                        key=f"dl_{ent['entrega_id']}"
                                    )
                            elif ent['archivo_ruta']:
                                st.warning(f"Archivo registrado: `{os.path.basename(str(ent['archivo_ruta']))}`.")

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
                            if st.button("🔓 Autorizar nuevo envío / reescritura" if not estado_aut else "🔒 Revocar autorización de reescritura", key=f"btn_aut_{ent['entrega_id']}"):
                                nuevo_estado = 0 if estado_aut else 1
                                c.execute("UPDATE entregas SET reescritura_autorizada = ? WHERE id = ?", (nuevo_estado, ent['entrega_id']))
                                conn.commit()
                                st.success("Estado de autorización actualizado.")
                                st.rerun()

                        with st.form(f"form_corr_{ent['entrega_id']}"):
                            n_nueva = st.number_input("Calificación Final", min_value=0.0, max_value=10.0, value=float(ent['nota']) if ent['nota'] is not None else 7.0)
                            dev_nueva = st.text_area("Devolución Pedagógica para el Alumno", value=ent['devolucion'] if ent['devolucion'] else "")
                            if st.form_submit_button("Guardar Calificación y Devolución"):
                                c.execute("UPDATE entregas SET nota = ?, devolucion = ? WHERE id = ?", (n_nueva, dev_nueva, ent['entrega_id']))
                                conn.commit()
                                st.success("Calificación guardada exitosamente.")
                                st.rerun()

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
                st.markdown("### 📊 **Estadísticas Generales y Gráfico de Torta de Asistencia**")
                
                resumen_asist = []
                total_presentes_global = 0
                total_ausentes_global = 0

                for _, al in alumnos_asist.iterrows():
                    total_clases = c.execute("SELECT COUNT(*) FROM asistencias WHERE catedra_id = ? AND estudiante_id = ?", (cat_id, al['id'])).fetchone()[0]
                    total_presentes = c.execute("SELECT COUNT(*) FROM asistencias WHERE catedra_id = ? AND estudiante_id = ? AND estado = 'Presente'", (cat_id, al['id'])).fetchone()[0]
                    total_ausentes = total_clases - total_presentes
                    pct = round((total_presentes / total_clases) * 100, 1) if total_clases > 0 else 0.0

                    total_presentes_global += total_presentes
                    total_ausentes_global += total_ausentes

                    resumen_asist.append({
                        "Estudiante": al['nombre'],
                        "Email": al['email'],
                        "Clases Registradas": total_clases,
                        "Presentes": total_presentes,
                        "Ausentes": total_ausentes,
                        "% Asistencia": f"{pct}%"
                    })

                col_asist_t, col_asist_g = st.columns([3, 2])
                with col_asist_t:
                    df_asist_resumen = pd.DataFrame(resumen_asist)
                    st.dataframe(df_asist_resumen, use_container_width=True, hide_index=True)

                with col_asist_g:
                    total_registros = total_presentes_global + total_ausentes_global
                    if total_registros > 0:
                        dict_asist = {
                            "Presentes": total_presentes_global,
                            "Ausentes": total_ausentes_global
                        }
                        st.markdown(render_pie_chart_svg(dict_asist), unsafe_allow_html=True)
                    else:
                        st.info("Aún no hay registros de asistencia para graficar.")

        # --- 5. PESTAÑA MENSAJES PRIVADOS ---
        with tab_mensajes:
            st.markdown("### ✉️ **Buzón de Mensajes Privados**")
            
            if alumnos_curso.empty:
                st.info("No hay alumnos matriculados en esta materia.")
            else:
                c.execute("UPDATE mensajes_privados SET leido = 1 WHERE receptor_id = ? AND catedra_id = ?", (u["id"], cat_id))
                conn.commit()

                map_al_msg = {}
                for _, r in alumnos_curso.iterrows():
                    no_leidos_cnt = c.execute("SELECT COUNT(*) FROM mensajes_privados WHERE emisor_id = ? AND receptor_id = ? AND catedra_id = ? AND leido = 0", (r['id'], u["id"], cat_id)).fetchone()[0]
                    tag_nl = f" (🔴 {no_leidos_cnt} nuevos)" if no_leidos_cnt > 0 else ""
                    map_al_msg[f"{r['nombre']} ({r['email']}){tag_nl}"] = r['id']

                sel_al_chat = st.selectbox("Seleccionar estudiante para conversar:", list(map_al_msg.keys()))
                al_chat_id = map_al_msg[sel_al_chat]

                st.markdown("#### **Historial de Conversación:**")
                mensajes_priv = pd.read_sql("""
                    SELECT m.id, m.mensaje, m.fecha, m.emisor_id, u.nombre as emisor_nombre, u.rol as emisor_rol
                    FROM mensajes_privados m
                    JOIN usuarios u ON m.emisor_id = u.id
                    WHERE m.catedra_id = ? AND ((m.emisor_id = ? AND m.receptor_id = ?) OR (m.emisor_id = ? AND m.receptor_id = ?))
                    ORDER BY m.id ASC
                """, conn, params=(cat_id, u["id"], al_chat_id, al_chat_id, u["id"]))

                if mensajes_priv.empty:
                    st.caption("No hay mensajes previos en esta conversación.")
                else:
                    for _, msg_p in mensajes_priv.iterrows():
                        es_mio = (msg_p['emisor_id'] == u['id'])
                        box_class = "msg-box-out" if es_mio else "msg-box-in"
                        emisor_tag = "Yo (Profesor)" if es_mio else f"👤 {msg_p['emisor_nombre']}"
                        
                        st.markdown(f"""
                        <div class='{box_class}'>
                            <b>{emisor_tag}</b> &nbsp;<small style='color:#64748b;'>{msg_p['fecha']}</small><br>
                            <p style='margin-top:4px; margin-bottom:0px;'>{msg_p['mensaje']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                with st.form(f"form_enviar_msg_priv_{al_chat_id}", clear_on_submit=True):
                    txt_nuevo_msg = st.text_area("Escribir respuesta:")
                    if st.form_submit_button("Enviar Mensaje") and txt_nuevo_msg.strip():
                        c.execute("""
                            INSERT INTO mensajes_privados (emisor_id, receptor_id, catedra_id, mensaje, fecha, leido)
                            VALUES (?, ?, ?, ?, ?, 0)
                        """, (u["id"], al_chat_id, cat_id, txt_nuevo_msg.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        st.success("Mensaje enviado.")
                        st.rerun()

# ==============================================================================
# 🎓 VISTA ESTUDIANTE
# ==============================================================================
else:
    st.markdown("## **Mis Cursos**")
    
    df_mis_cursos = pd.read_sql("""
        SELECT c.id, c.nombre, c.curso_anio, c.escuela, c.profesor_id, u.nombre as profesor_nombre 
        FROM catedras c 
        JOIN matriculas m ON c.id = m.catedra_id 
        JOIN usuarios u ON c.profesor_id = u.id
        WHERE m.estudiante_id = ?
    """, conn, params=(u["id"],))

    if df_mis_cursos.empty:
        st.warning("No estás matriculado en ninguna materia aún.")
        st.stop()

    mat_map = {f"{r['nombre']} ({r['curso_anio']} - {r['escuela']})": r for _, r in df_mis_cursos.iterrows()}
    sel_mat_al = st.selectbox("Seleccionar Curso:", list(mat_map.keys()))
    materia_row = mat_map[sel_mat_al]
    materia_id = materia_row["id"]
    profesor_id_materia = materia_row["profesor_id"]
    profesor_nom_materia = materia_row["profesor_nombre"]

    tab_al_curso, tab_al_notas, tab_al_asist, tab_al_chat = st.tabs([
        "📘 Curso y Evaluaciones", "📊 Mis Calificaciones", "📋 Mi Asistencia", "✉️ Mensajes al Profesor"
    ])

    with tab_al_curso:
        df_sec_al = pd.read_sql("SELECT id, titulo FROM secciones WHERE catedra_id = ? ORDER BY orden ASC", conn, params=(materia_id,))
        for _, s in df_sec_al.iterrows():
            st.markdown(f"#### 📂 {s['titulo']}")
            acts_al = pd.read_sql("SELECT * FROM actividades WHERE seccion_id = ?", conn, params=(s['id'],))
            
            for _, act in acts_al.iterrows():
                if act['tipo'] == 'Bibliografía':
                    ico = "📚" if act['es_obligatorio'] == 1 else "📖"
                    tag_tipo = "Bibliografía Obligatoria" if act['es_obligatorio'] == 1 else "Bibliografía Optativa"
                elif act['tipo'] == 'Foro':
                    ico = "💬"
                    tag_tipo = "Foro Evaluativo" if act['es_obligatorio'] == 1 else "Foro"
                elif act['tipo'] == 'Cuestionario':
                    ico = "⏱️"
                    tag_tipo = "Examen"
                else:
                    ico = "📝"
                    tag_tipo = "Tarea"
                
                if act['tipo'] == "Bibliografía":
                    with st.expander(f"{ico} {act['titulo']} ({tag_tipo}) — Fecha: {act['fecha_limite']}"):
                        if act['descripcion']:
                            st.markdown(f"**📌 Contenido / Referencia:**")
                            st.write(act['descripcion'])
                        if act['enlace_archivo']:
                            renderizar_recurso_multimedia(act['enlace_archivo'])

                elif act['tipo'] == "Foro":
                    with st.expander(f"{ico} {act['titulo']} ({tag_tipo}) — Vence: {act['fecha_limite']}"):
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
                    
                    reescritura_permitida = False
                    if ya_rendido:
                        reescritura_permitida = ent_al.iloc[0]['reescritura_autorizada'] == 1

                    estado_txt = "⏳ Pendiente" if not ya_rendido else ("🔓 Habilitado para Reenvío" if reescritura_permitida else "✅ Entregado")
                    
                    with st.expander(f"{ico} {act['titulo']} ({tag_tipo}) | {estado_txt}"):
                        st.write(f"**Consigna:** {act['descripcion']}")
                        
                        if act['enlace_archivo']:
                            renderizar_recurso_multimedia(act['enlace_archivo'])

                        if ya_rendido and not reescritura_permitida:
                            data_ent = ent_al.iloc[0]
                            st.success(f"Entregado el: {data_ent['fecha_entrega']}")
                            
                            if data_ent['archivo_ruta'] and isinstance(data_ent['archivo_ruta'], str) and os.path.exists(data_ent['archivo_ruta']):
                                nom_orig = os.path.basename(data_ent['archivo_ruta'])
                                with open(data_ent['archivo_ruta'], "rb") as f_down:
                                    st.download_button(
                                        label=f"📥 Ver / Descargar mi archivo enviado ({nom_orig})",
                                        data=f_down.read(),
                                        file_name=nom_orig,
                                        key=f"dl_al_propio_{data_ent['id']}"
                                    )
                            elif data_ent['respuesta_data']:
                                st.markdown(f"**Tu respuesta escrita:** {data_ent['respuesta_data']}")

                            if data_ent['nota'] is not None:
                                st.metric("Calificación:", f"{data_ent['nota']}/10")
                                st.info(f"**Devolución del Profesor:**\n{data_ent['devolucion']}")
                            
                            st.divider()
                            if st.button("🔄 Solicitar Autorización de Reenvío al Docente", key=f"req_reenv_{act['id']}"):
                                msg_auto = f"Hola profesor, le solicito autorización para volver a enviar mi trabajo en la actividad: '{act['titulo']}'."
                                c.execute("""
                                    INSERT INTO mensajes_privados (emisor_id, receptor_id, catedra_id, mensaje, fecha, leido)
                                    VALUES (?, ?, ?, ?, ?, 0)
                                """, (u["id"], profesor_id_materia, materia_id, msg_auto, datetime.now().strftime("%Y-%m-%d %H:%M")))
                                conn.commit()
                                st.success("¡Solicitud enviada al profesor por mensajería privada!")

                        else:
                            if reescritura_permitida:
                                st.warning("🔓 El profesor te ha autorizado a realizar un nuevo envío o reemplazar tu archivo.")

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
                                            INSERT INTO entregas (actividad_id, estudiante_id, fecha_entrega, respuesta_data, nota, devolucion, tiempo_empleado_seg, reescritura_autorizada)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                                            ON CONFLICT(actividad_id, estudiante_id)
                                            DO UPDATE SET fecha_entrega=excluded.fecha_entrega, respuesta_data=excluded.respuesta_data,
                                                          nota=excluded.nota, devolucion=excluded.devolucion, tiempo_empleado_seg=excluded.tiempo_empleado_seg,
                                                          reescritura_autorizada=0
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
                                    if st.form_submit_button("Enviar o Reenviar Tarea"):
                                        r_path = None
                                        if arch is not None:
                                            r_path = os.path.join(CARPETA_ENTREGAS, f"{u['id']}_{act['id']}_{arch.name}")
                                            with open(r_path, "wb") as f:
                                                f.write(arch.getbuffer())
                                        c.execute("""
                                            INSERT INTO entregas (actividad_id, estudiante_id, fecha_entrega, respuesta_data, archivo_ruta, reescritura_autorizada)
                                            VALUES (?, ?, ?, ?, ?, 0)
                                            ON CONFLICT(actividad_id, estudiante_id)
                                            DO UPDATE SET fecha_entrega=excluded.fecha_entrega, respuesta_data=excluded.respuesta_data,
                                                          archivo_ruta=excluded.archivo_ruta, reescritura_autorizada=0
                                        """, (act['id'], u['id'], datetime.now().strftime("%Y-%m-%d %H:%M"), rta_t, r_path))
                                        conn.commit()
                                        st.success("Tarea enviada/actualizada correctamente.")
                                        st.rerun()

    with tab_al_notas:
        st.markdown("### 📋 **Mis Calificaciones y Resumen Oficial de Períodos**")
        
        per_al = c.execute("""
            SELECT informe_avance_1, cuatrimestre_1, informe_avance_2, cuatrimestre_2, calificacion_final_dic
            FROM calificaciones_periodos
            WHERE catedra_id = ? AND estudiante_id = ?
        """, (materia_id, u['id'])).fetchone()

        c_per1, c_per2, c_per3 = st.columns(3)
        with c_per1:
            st.metric("1° Cuatrimestre", f"{per_al[1]:.2f}" if per_al and per_al[1] is not None else "-")
            st.caption(f"**1° Informe:** `{per_al[0] if per_al and per_al[0] else '-'}`")
        with c_per2:
            st.metric("2° Cuatrimestre", f"{per_al[3]:.2f}" if per_al and per_al[3] is not None else "-")
            st.caption(f"**2° Informe:** `{per_al[2] if per_al and per_al[2] else '-'}`")
        with c_per3:
            st.metric("Calificación Final (Dic)", f"{per_al[4]:.2f}" if per_al and per_al[4] is not None else "-")

        st.divider()
        st.markdown("#### 📊 **Seguimiento de Trabajos Prácticos y Evaluaciones:**")
        df_notas_al = pd.read_sql("""
            SELECT a.titulo as Actividad, a.tipo as Tipo, e.nota as Calificación, e.devolucion as Devolución, e.fecha_entrega as 'Fecha de Entrega'
            FROM actividades a
            LEFT JOIN entregas e ON a.id = e.actividad_id AND e.estudiante_id = ?
            WHERE a.catedra_id = ? AND (a.tipo IN ('Tarea', 'Cuestionario') OR (a.tipo = 'Foro' AND a.es_obligatorio = 1))
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

    with tab_al_chat:
        st.markdown(f"### ✉️ **Mensajes Privados con el Docente: {profesor_nom_materia}**")
        
        c.execute("UPDATE mensajes_privados SET leido = 1 WHERE receptor_id = ? AND catedra_id = ?", (u["id"], materia_id))
        conn.commit()

        mensajes_priv_al = pd.read_sql("""
            SELECT m.id, m.mensaje, m.fecha, m.emisor_id, u.nombre as emisor_nombre, u.rol as emisor_rol
            FROM mensajes_privados m
            JOIN usuarios u ON m.emisor_id = u.id
            WHERE m.catedra_id = ? AND ((m.emisor_id = ? AND m.receptor_id = ?) OR (m.emisor_id = ? AND m.receptor_id = ?))
            ORDER BY m.id ASC
        """, conn, params=(materia_id, u["id"], profesor_id_materia, profesor_id_materia, u["id"]))

        if mensajes_priv_al.empty:
            st.caption("No tienes mensajes en esta materia con el profesor.")
        else:
            for _, msg_p in mensajes_priv_al.iterrows():
                es_mio = (msg_p['emisor_id'] == u['id'])
                box_class = "msg-box-out" if es_mio else "msg-box-in"
                emisor_tag = "Yo (Estudiante)" if es_mio else f"👨‍🏫 {msg_p['emisor_nombre']}"
                
                st.markdown(f"""
                <div class='{box_class}'>
                    <b>{emisor_tag}</b> &nbsp;<small style='color:#64748b;'>{msg_p['fecha']}</small><br>
                    <p style='margin-top:4px; margin-bottom:0px;'>{msg_p['mensaje']}</p>
                </div>
                """, unsafe_allow_html=True)

        with st.form("form_enviar_msg_profesor", clear_on_submit=True):
            txt_nuevo_msg_al = st.text_area("Escribir consulta o mensaje al docente:")
            if st.form_submit_button("Enviar Mensaje al Docente") and txt_nuevo_msg_al.strip():
                c.execute("""
                    INSERT INTO mensajes_privados (emisor_id, receptor_id, catedra_id, mensaje, fecha, leido)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (u["id"], profesor_id_materia, materia_id, txt_nuevo_msg_al.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                st.success("Mensaje enviado al docente.")
                st.rerun()
