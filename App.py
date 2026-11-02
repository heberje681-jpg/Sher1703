"""Para Sher — app romántica en Streamlit (una sola página, cielo estrellado)."""
import html
import random
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageOps

import storage as db

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# ───────────── Personaliza aquí ─────────────
YO, ELLA = "Heber", "Sher"
PLAYLIST_ID = "6lMxGgpesZcqzTQR7iOKFz"  # open.spotify.com/playlist/<ESTE_ID>?si=...
LAT, LON = 20.6597, -103.3496           # Guadalajara, Jalisco
DEDICATORIA = "Así se veía el cielo sobre Guadalajara la noche del 3 de diciembre de 2022."
SEMILLA_PLANES = [
    {"id": "video", "texto": "Hacer un video juntos 🎬", "hecho": False},
    {"id": "vacaciones", "texto": "Ir de vacaciones ✈️", "hecho": False},
    {"id": "acampar", "texto": "Acampar bajo las estrellas ⛺", "hecho": False},
]
# ─────────────────────────────────────────────
GDL = timezone(timedelta(hours=-6))   # hora de Guadalajara en dic 2022
SIN = timezone(timedelta(hours=-7))   # hora de Sinaloa (fechas de las cartas)
ORO, BLANCO = "#F2B35E", "#FFFFFF"

st.set_page_config(page_title=f"Para {ELLA}", page_icon="🌙", layout="centered")

def _estrellas(n, titilan):
    r, out = random.Random(11 if not titilan else 23), []
    for _ in range(n):
        s = r.choice([0, 1, 1]) if titilan else 0
        out.append(f"{r.uniform(0, 100):.1f}vw {r.uniform(0, 100):.1f}vh 0 {s}px rgba(255,255,255,{r.uniform(.45, 1):.2f})")
    return ",".join(out)

# CSS Actualizado: Fondo negro, fuentes modernas, botones cuadrados/limpios
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Montserrat:wght@300;400;500&family=Caveat:wght@500&display=swap');
.stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button,
.stApp [data-testid="stCaptionContainer"] {font-family:'Montserrat',sans-serif; font-weight:300; color:#E0E0E0;}
.stApp {background: radial-gradient(circle at 50% 50%, #0d111a 0%, #000000 100%) fixed;}
.stApp::before, .stApp::after {content:""; position:fixed; top:0; left:0; width:1px; height:1px; pointer-events:none; z-index:0;}
.stApp::before {box-shadow:__FIJAS__;}
.stApp::after {box-shadow:__BRILLAN__; animation:titila 4s ease-in-out infinite alternate;}
@keyframes titila {from {opacity:.2;} to {opacity:1;}}
.block-container {position:relative; z-index:1; max-width:760px; padding-top:1rem;}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {display:none;}
header {background:transparent !important;}
.hero {text-align:center; padding:2rem 0 .5rem;}
.hero .t {font-family:'Cinzel',serif; font-size:4rem; line-height:1.1; color:#fff; font-weight:600; text-shadow:0 0 20px rgba(255,255,255,.2);}
.hero .s {color:#A0A0A0; font-size:1rem; letter-spacing:.05em; margin-top:.5rem;}
.sec {font-family:'Cinzel',serif; font-size:2.2rem; text-align:center; color:#fff; margin-top:4rem;}
.sec::before {content:"✦"; display:block; color:#F2B35E; font-size:1.2rem; margin-bottom:.4rem;}
.secsub {text-align:center; color:#888; font-size:.9rem; margin:.2rem 0 1.5rem; text-transform:uppercase; letter-spacing:2px;}
.stButton button {background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.15); border-radius:8px; padding:.4rem 1rem; transition:all .3s ease; backdrop-filter:blur(5px);}
.stButton button:hover {border-color:#fff; background:rgba(255,255,255,.15); transform:translateY(-2px);}
.stButton button p {color:#fff; font-weight:400; letter-spacing:1px;}
.stFormSubmitButton button {background:rgba(242,179,94,.15); border:1px solid #F2B35E; border-radius:8px;}
.stFormSubmitButton button p {color:#F2B35E; font-weight:500;}
.stTextInput input, .stTextArea textarea {border-radius:8px; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.2); color:#fff;}
[data-testid="stExpander"] {border:1px solid rgba(255,255,255,.1); border-radius:12px; background:rgba(255,255,255,.03);}
[data-testid="stCheckbox"] {background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.1); border-radius:8px; padding:.7rem 1rem; margin-bottom:.4rem;}
[data-testid="stCheckbox"]:hover {border-color:#F2B35E;}
[data-testid="stImage"] img {width:100%; border-radius:12px; box-shadow:0 8px 30px rgba(0,0,0,.8);}
.nota {font-family:'Caveat',cursive; font-size:1.8rem; line-height:1.4; color:#fff; background:rgba(255,255,255,.04);
  border-left:3px solid var(--c); border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1rem;}
.pie {font-family:'Montserrat',sans-serif; text-align:center; color:#A0A0A0; font-size:0.9rem; margin-top:.7rem;}
.dedic {text-align:center; color:#A0A0A0; margin-bottom:.8rem; font-style:italic;}
</style>""".replace("__FIJAS__", _estrellas(150, False)).replace("__BRILLAN__", _estrellas(50, True))
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(f"""<div class="hero"><div class="t">Para {html.escape(ELLA)}</div>
<div class="s">Un cielo, un álbum y todo lo que nos falta por vivir.</div></div>""",
            unsafe_allow_html=True)

if not db.obtener().persistente:
    st.info("Modo prueba: lo que guardes se borra al reiniciar la app.")
if "aviso" in st.session_state:
    st.success(st.session_state.pop("aviso"))

def seccion(titulo, sub):
    st.markdown(f'<div class="sec">{titulo}</div><div class="secsub">{sub}</div>', unsafe_allow_html=True)

# ───────────── Datos del cielo ─────────────
ESTRELLAS = {
    "Betelgeuse": (5.919, 7.407, .5), "Rigel": (5.242, -8.202, .1), "Bellatrix": (5.419, 6.350, 1.6),
    "Mintaka": (5.533, -.299, 2.2), "Alnilam": (5.604, -1.202, 1.7), "Alnitak": (5.679, -1.943, 1.8),
    "Aldebaran": (4.599, 16.509, .9), "Pléyades": (3.791, 24.105, 1.6),
    "Sirius": (6.752, -16.716, -1.5), "Procyon": (7.655, 5.225, .4),
    "Castor": (7.577, 31.888, 1.6), "Pollux": (7.755, 28.026, 1.1),
    "Capella": (5.278, 45.998, .1), "Polaris": (2.530, 89.264, 2.0),
    "Vega": (18.616, 38.784, 0.), "Deneb": (20.690, 45.280, 1.3), "Altair": (19.846, 8.868, .8)
}
CONSTELACIONES = {
    "Orión": [["Betelgeuse", "Alnitak", "Alnilam", "Mintaka", "Bellatrix"], ["Alnitak", "Rigel", "Mintaka"]],
    "Tauro": [["Aldebaran"]],
    "Can Mayor": [["Sirius"]],
    "Osa Menor": [["Polaris"]]
}
CON_NOMBRE = {"Sirius", "Betelgeuse", "Rigel", "Aldebaran", "Capella", "Procyon", "Pollux", "Vega", "Polaris"}

@st.cache_data(show_spinner=False)
def mapa_png(hora):
    t = datetime(2022, 12, 3, hora, 0, tzinfo=GDL).astimezone(timezone.utc)
    d = 2440587.5 + t.timestamp() / 86400 - 2451545.0
    lst = np.radians(((18.697374558 + 24.06570982441908 * d) % 24 + LON / 15) % 24 * 15)
    lat = np.radians(LAT)
    pos = {}
    for n, (ra, dec, mag) in ESTRELLAS.items():
        dec, h = np.radians(dec), lst - np.radians(ra * 15)
        alt = np.arcsin(np.sin(dec) * np.sin(lat) + np.cos(dec) * np.cos(lat) * np.cos(h))
        az = np.arctan2(-np.cos(dec) * np.sin(h), np.sin(dec) * np.cos(lat) - np.cos(dec) * np.sin(lat) * np.cos(h))
        r = 1 - alt / (np.pi / 2)
        pos[n] = (-r * np.sin(az), r * np.cos(az), alt > 0, mag) 

    fig, ax = plt.subplots(figsize=(7, 7), dpi=180)
    fig.patch.set_alpha(0)
    ax.add_patch(plt.Circle((0, 0), 1, color="#030407"))
    ax.add_patch(plt.Circle((0, 0), 1, fill=False, ec=BLANCO, lw=1, alpha=0.3))
    for nombre, cadenas in CONSTELACIONES.items():
        vistas = set()
        for c in cadenas:
            for a, b in zip(c, c[1:]):
                if pos[a][2] and pos[b][2]:
                    ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color=BLANCO, alpha=.3, lw=1)
                    vistas |= {a, b}
        if vistas:
            ax.text(np.mean([pos[s][0] for s in vistas]), np.mean([pos[s][1] for s in vistas]) - .045, nombre,
                    color=BLANCO, fontsize=7.5, style="italic", ha="center", alpha=.6)
    vis = [(x, y, m, n) for n, (x, y, ok, m) in pos.items() if ok]
    ax.scatter([v[0] for v in vis], [v[1] for v in vis],
               s=[8 * np.clip(4.2 - v[2], .8, 6) ** 2 for v in vis], color="#FFF", zorder=3)
    for x, y, _, n in vis:
        if n in CON_NOMBRE:
            ax.text(x + .02, y + .02, n, color="#A0A0A0", fontsize=7)
    for txt, x, y in (("N", 0, 1.07), ("E", -1.08, 0), ("O", 1.08, 0), ("S", 0, -1.1)):
        ax.text(x, y, txt, color=BLANCO, fontsize=10, ha="center", va="center", family="serif", alpha=0.5)
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15); ax.set_aspect("equal"); ax.axis("off")
    buf = BytesIO(); fig.savefig(buf, format="png", transparent=True, bbox_inches="tight"); plt.close(fig)
    return buf.getvalue()

def preparar_foto(archivo):
    img = ImageOps.exif_transpose(Image.open(archivo)).convert("RGB")
    img.thumbnail((1600, 1600))
    buf = BytesIO(); img.save(buf, "JPEG", quality=82, optimize=True)
    return buf.getvalue()

def mover(delta, n):
    st.session_state.foto_i = (st.session_state.get("foto_i", 0) + delta) % n

# ───────────── Nuestro cielo ─────────────
seccion("Nuestro cielo", "La noche que lo cambió todo")
st.markdown(f'<div class="dedic">{DEDICATORIA}</div>', unsafe_allow_html=True)
hora = st.select_slider("Hora local", options=[19, 20, 21, 22, 23], value=21, format_func=lambda h: f"{h}:00")
st.image(mapa_png(hora))

# ───────────── Nuestro álbum ─────────────
seccion("Nuestro álbum", "Lugares y momentos")
eliminadas = db.leer_json("eliminadas.json", [])
fotos_todas = db.listar_fotos()
fotos = [f for f in fotos_todas if f not in eliminadas]
pies = db.leer_json("album.json", {})

if fotos:
    i = st.session_state.get("foto_i", 0) % len(fotos)
    
    # Foto Principal
    st.image(db.bytes_foto(fotos[i]), use_container_width=True)
    st.markdown(f'<div class="pie">{html.escape(pies.get(fotos[i], ""))}</div>', unsafe_allow_html=True)
    
    # Controles del carrusel
    col_prev, col_count, col_next, col_del = st.columns([1, 1, 1, 1])
    col_prev.button("⬅", on_click=mover, args=(-1, len(fotos)), key="prev", use_container_width=True)
    col_count.markdown(f"<div style='text-align:center; padding-top:10px; color:#888;'>{i + 1} / {len(fotos)}</div>", unsafe_allow_html=True)
    col_next.button("Siguiente", on_click=mover, args=(1, len(fotos)), key="btn_siguiente", use_container_width=True)
    
    if col_del.button("🗑️ Eliminar", use_container_width=True):
        eliminadas.append(fotos[i])
        db.guardar_json("eliminadas.json", eliminadas)
        st.session_state.foto_i = 0
        st.session_state.aviso = "Foto eliminada."
        st.rerun()

    # Script JS para cambiar la foto automáticamente cada 30 segundos
    components.html("""
    <script>
    setTimeout(() => {
        const btns = Array.from(window.parent.document.querySelectorAll('button'));
        const nextBtn = btns.find(b => b.innerText.includes('Siguiente'));
        if(nextBtn) nextBtn.click();
    }, 30000);
    </script>
    """, height=0)

    # Cuadrícula inferior con todas las fotos
    st.markdown("<br><p style='text-align:center; font-size:0.8rem; letter-spacing:1px; color:#555;'>TODAS LAS FOTOS</p>", unsafe_allow_html=True)
    grid_cols = st.columns(3)
    for idx, f in enumerate(fotos):
        with grid_cols[idx % 3]:
            st.image(db.bytes_foto(f), use_container_width=True)

else:
    st.markdown('<div class="pie">Aquí van a vivir nuestros viajes. Sube la primera foto.</div>', unsafe_allow_html=True)

with st.expander("📸 Subir fotos nuevas", expanded=not fotos):
    with st.form("subir", clear_on_submit=True):
        archivos = st.file_uploader("Elige fotos de tu galería o toma una",
                                    type=["jpg", "jpeg", "png", "webp", "heic"], accept_multiple_files=True)
        pie = st.text_input("Pie de foto (opcional)", placeholder="Ej. Nuestro viaje...")
        guardar = st.form_submit_button("Guardar foto")
    if guardar and not archivos:
        st.warning("Elige al menos una foto.")
    elif guardar:
        with st.spinner("Guardando…"):
            nuevos = dict(pies)
            for f in archivos:
                try:
                    nombre = f"{datetime.now(SIN):%Y%m%d%H%M%S}_{uuid.uuid4().hex[:5]}.jpg"
                    db.guardar_foto(nombre, preparar_foto(f))
                    if pie.strip():
                        nuevos[nombre] = pie.strip()
                except Exception as e:
                    st.error(f"No pude guardar {f.name}: {e}")
            db.guardar_json("album.json", nuevos)
        st.session_state.foto_i = 0
        st.session_state.aviso = "Fotos guardadas 📸"
        st.rerun()

# ───────────── Buzón abierto ─────────────
seccion("Buzón abierto", "Notas sin candados")
with st.expander("✍️ Escribir una carta"):
    with st.form("nota", clear_on_submit=True):
        autor = st.radio("Escribe como", [YO, ELLA], horizontal=True)
        titulo = st.text_input("Título", placeholder="Para cuando me extrañes…")
        texto = st.text_area("Tu carta", height=200, placeholder="Escribe todo lo que quieras...")
        enviar = st.form_submit_button("Guardar en el buzón")
    if enviar and texto.strip():
        notas = db.leer_json("notas.json", [])
        notas.append({"autor": autor, "titulo": titulo.strip(), "texto": texto.strip(),
                      "fecha": f"{datetime.now(SIN):%d/%m/%Y %H:%M}"})
        db.guardar_json("notas.json", notas)
        st.session_state.aviso = "Carta guardada 💌"
        st.rerun()

notas = db.leer_json("notas.json", [])
for k, n in enumerate(reversed(notas)):
    with st.expander(f"{n['titulo'] or 'Sin título'} · {n['autor']} · {n['fecha']}", expanded=(k == 0)):
        color = ORO if n["autor"] == YO else BLANCO
        cuerpo = html.escape(n["texto"]).replace("\n", "<br>")
        st.markdown(f'<div class="nota" style="--c:{color}">{cuerpo}</div>', unsafe_allow_html=True)

# ───────────── Soundtrack y planes ─────────────
seccion("Nuestro soundtrack", "Nuestra playlist")
url = f"https://open.spotify.com/embed/playlist/{PLAYLIST_ID}?utm_source=generator&theme=0"
if hasattr(st, "iframe"):
    st.iframe(url, height=352)
else:
    components.iframe(url, height=352)

seccion("Planes por tachar", "Lo que haremos juntos")
planes = db.leer_json("planes_v2.json", SEMILLA_PLANES)

def marcar(i):
    planes[i]["hecho"] = st.session_state[f"p_{planes[i]['id']}"]
    db.guardar_json("planes_v2.json", planes)

for i, p in enumerate(planes):
    clave = f"p_{p['id']}"
    st.session_state[clave] = p["hecho"]
    st.checkbox(f"~~{p['texto']}~~" if p["hecho"] else p["texto"], key=clave, on_change=marcar, args=(i,))

with st.expander("➕ Agregar un plan nuevo"):
    with st.form("nuevo_plan", clear_on_submit=True):
        nuevo = st.text_input("Nuevo plan")
        if st.form_submit_button("Agregar plan") and nuevo.strip():
            planes.append({"id": uuid.uuid4().hex[:8], "texto": nuevo.strip(), "hecho": False})
            db.guardar_json("planes_v2.json", planes)
            st.rerun()
