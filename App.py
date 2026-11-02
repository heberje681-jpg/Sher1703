"""Para Sher — app romántica en Streamlit."""
import html
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
LAT, LON = 20.6597, -103.3496      # Guadalajara, Jalisco
DEDICATORIA = "Así se veía el cielo sobre Guadalajara la noche del 3 de diciembre de 2022."
SEMILLA_PLANES = [
    {"id": "ruta", "texto": "Una ruta larga en carro, con nuestra playlist y sin prisa", "hecho": False},
    {"id": "ahome", "texto": "Ir por mariscos a Ahome", "hecho": False},
]
# ─────────────────────────────────────────────
GDL = timezone(timedelta(hours=-6))   # hora de Guadalajara en dic 2022
SIN = timezone(timedelta(hours=-7))   # hora de Sinaloa (para las fechas de las cartas)
ORO, ROSA = "#F2B35E", "#E58C9A"

st.set_page_config(page_title=f"Para {ELLA}", page_icon="🌙", layout="centered")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,500;1,600&family=Figtree:wght@400;600&display=swap');
.stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button {font-family:'Figtree',sans-serif;}
.stApp {background:radial-gradient(120% 60% at 50% 0%, #4A2038 0%, #2A1424 60%);}
.block-container {max-width:760px; padding-top:1.5rem;}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {display:none;}
header {background:transparent !important;}
.hero {text-align:center; padding:1.5rem 0 1rem;}
.hero .t {font-family:'Cormorant Garamond',serif; font-style:italic; font-weight:600; font-size:3.6rem; line-height:1.05; color:#F7E6DA;}
.hero .s {font-family:'Cormorant Garamond',serif; font-size:1.3rem; color:#E9C9B5; margin-top:.4rem;}
.stTabs [data-baseweb="tab-list"] {gap:.4rem; flex-wrap:wrap; border:0;}
.stTabs [data-baseweb="tab"] {background:#3A1D31; border-radius:999px; padding:.45rem 1rem; height:auto;}
.stTabs [aria-selected="true"] {background:#F2B35E;}
.stTabs [aria-selected="true"] p {color:#2A1424; font-weight:600;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display:none;}
.stButton button, .stFormSubmitButton button {border-radius:999px; border:0; background:#E58C9A;}
.stButton button p, .stFormSubmitButton button p {color:#2A1424; font-weight:600;}
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {border-radius:16px;}
[data-testid="stImage"] img {width:100%; border-radius:26px;}
[data-testid="stExpander"] {border-radius:20px; background:#331A2B; border:0;}
.nota {font-family:'Cormorant Garamond',serif; font-size:1.3rem; line-height:1.6; background:#3A1D31;
  border-radius:22px; padding:1.1rem 1.4rem; border-left:6px solid var(--c);}
.pie {font-family:'Cormorant Garamond',serif; font-style:italic; font-size:1.3rem; text-align:center; color:#E9C9B5;}
.dedic {font-family:'Cormorant Garamond',serif; font-style:italic; font-size:1.35rem; text-align:center; color:#E9C9B5;}
</style>""", unsafe_allow_html=True)

st.markdown(f"""<div class="hero"><div class="t">Para {html.escape(ELLA)}</div>
<div class="s">Un cielo, un álbum, una playlist y todo lo que nos falta por vivir.</div></div>""",
            unsafe_allow_html=True)

if not db.obtener().persistente:
    st.info("Modo prueba: lo que guardes se borra al reiniciar la app. "
            "Configura los secrets de GitHub para que todo quede guardado.")
if "aviso" in st.session_state:
    st.success(st.session_state.pop("aviso"))

# ───────────── Datos del cielo ─────────────
# nombre: (AR en horas, Dec en grados, magnitud)
ESTRELLAS = {
    "Betelgeuse": (5.919, 7.407, .5), "Rigel": (5.242, -8.202, .1), "Bellatrix": (5.419, 6.350, 1.6),
    "Mintaka": (5.533, -.299, 2.2), "Alnilam": (5.604, -1.202, 1.7), "Alnitak": (5.679, -1.943, 1.8),
    "Saiph": (5.796, -9.670, 2.1), "Meissa": (5.585, 9.934, 3.5),
    "Aldebaran": (4.599, 16.509, .9), "Elnath": (5.438, 28.608, 1.7), "Zeta Tau": (5.627, 21.143, 3.0),
    "Gamma Tau": (4.330, 15.628, 3.6), "Pléyades": (3.791, 24.105, 1.6),
    "Sirius": (6.752, -16.716, -1.5), "Adhara": (6.977, -28.972, 1.5), "Wezen": (7.140, -26.393, 1.8),
    "Mirzam": (6.378, -17.956, 2.0), "Procyon": (7.655, 5.225, .4), "Gomeisa": (7.452, 8.289, 2.9),
    "Castor": (7.577, 31.888, 1.6), "Pollux": (7.755, 28.026, 1.1),
    "Capella": (5.278, 45.998, .1), "Menkalinan": (5.992, 44.947, 1.9),
    "Theta Aur": (5.995, 37.213, 2.6), "Iota Aur": (4.950, 33.166, 2.7),
    "Caph": (.153, 59.150, 2.3), "Schedar": (.675, 56.537, 2.2), "Gamma Cas": (.945, 60.717, 2.4),
    "Ruchbah": (1.430, 60.235, 2.7), "Segin": (1.907, 63.670, 3.4),
    "Dubhe": (11.062, 61.751, 1.8), "Merak": (11.031, 56.382, 2.4), "Phecda": (11.897, 53.695, 2.4),
    "Megrez": (12.257, 57.033, 3.3), "Alioth": (12.900, 55.960, 1.8), "Mizar": (13.399, 54.925, 2.2),
    "Alkaid": (13.792, 49.313, 1.9),
    "Regulus": (10.139, 11.967, 1.4), "Algieba": (10.333, 19.842, 2.1), "Zosma": (11.235, 20.524, 2.6),
    "Denebola": (11.818, 14.572, 2.1),
    "Markab": (23.079, 15.205, 2.5), "Scheat": (23.063, 28.083, 2.4), "Alpheratz": (.139, 29.091, 2.1),
    "Algenib": (.220, 15.184, 2.8), "Mirach": (1.162, 35.621, 2.1), "Almach": (2.065, 42.330, 2.3),
    "Mirfak": (3.405, 49.861, 1.8), "Algol": (3.136, 40.956, 2.1),
    "Vega": (18.616, 38.784, 0.), "Deneb": (20.690, 45.280, 1.3), "Altair": (19.846, 8.868, .8),
    "Fomalhaut": (22.961, -29.622, 1.2), "Polaris": (2.530, 89.264, 2.0), "Arcturus": (14.261, 19.182, 0.),
    "Spica": (13.420, -11.161, 1.0), "Canopus": (6.399, -52.696, -.7),
}
CONSTELACIONES = {
    "Orión": [["Meissa", "Betelgeuse", "Alnitak", "Alnilam", "Mintaka", "Bellatrix", "Meissa"],
              ["Alnitak", "Saiph", "Rigel", "Mintaka"]],
    "Tauro": [["Gamma Tau", "Aldebaran", "Zeta Tau"], ["Aldebaran", "Elnath"]],
    "Can Mayor": [["Mirzam", "Sirius", "Wezen", "Adhara"]],
    "Can Menor": [["Gomeisa", "Procyon"]],
    "Géminis": [["Castor", "Pollux"]],
    "Auriga": [["Capella", "Menkalinan", "Theta Aur", "Elnath", "Iota Aur", "Capella"]],
    "Casiopea": [["Caph", "Schedar", "Gamma Cas", "Ruchbah", "Segin"]],
    "Osa Mayor": [["Dubhe", "Merak", "Phecda", "Megrez", "Dubhe"], ["Megrez", "Alioth", "Mizar", "Alkaid"]],
    "Leo": [["Regulus", "Algieba", "Zosma", "Denebola"]],
    "Pegaso": [["Markab", "Scheat", "Alpheratz", "Algenib", "Markab"]],
    "Andrómeda": [["Alpheratz", "Mirach", "Almach"]],
    "Perseo": [["Almach", "Mirfak", "Algol"]],
    "Triángulo de verano": [["Vega", "Deneb", "Altair", "Vega"]],
}
CON_NOMBRE = {"Sirius", "Betelgeuse", "Rigel", "Aldebaran", "Capella", "Procyon", "Pollux", "Vega",
              "Polaris", "Canopus", "Pléyades", "Fomalhaut", "Arcturus", "Altair", "Deneb"}


@st.cache_data(show_spinner=False)
def mapa_png(hora):
    """Cielo visible desde Guadalajara el 3-dic-2022 a la hora local indicada (proyección cenital)."""
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
        pos[n] = (-r * np.sin(az), r * np.cos(az), alt > 0, mag)  # este a la izquierda, como al mirar arriba

    fig, ax = plt.subplots(figsize=(7, 7), dpi=180)
    fig.patch.set_alpha(0)
    ax.add_patch(plt.Circle((0, 0), 1, color="#150B20"))
    ax.add_patch(plt.Circle((0, 0), 1, fill=False, ec=ORO, lw=1.6))
    for nombre, cadenas in CONSTELACIONES.items():
        vistas = set()
        for c in cadenas:
            for a, b in zip(c, c[1:]):
                if pos[a][2] and pos[b][2]:
                    ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color=ORO, alpha=.5, lw=1)
                    vistas |= {a, b}
        if vistas:
            ax.text(np.mean([pos[s][0] for s in vistas]), np.mean([pos[s][1] for s in vistas]) - .045, nombre,
                    color=ROSA, fontsize=7.5, style="italic", ha="center", alpha=.9)
    vis = [(x, y, m, n) for n, (x, y, ok, m) in pos.items() if ok]
    ax.scatter([v[0] for v in vis], [v[1] for v in vis],
               s=[8 * np.clip(4.2 - v[2], .8, 6) ** 2 for v in vis], color="#FFF1DC", zorder=3)
    for x, y, _, n in vis:
        if n in CON_NOMBRE:
            ax.text(x + .02, y + .02, n, color="#F7E6DA", fontsize=7)
    for txt, x, y in (("N", 0, 1.07), ("E", -1.08, 0), ("O", 1.08, 0), ("S", 0, -1.1)):
        ax.text(x, y, txt, color=ORO, fontsize=13, ha="center", va="center", family="serif")
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


t1, t2, t3, t4 = st.tabs(["🌌 Nuestro Cielo", "📷 Nuestro Álbum", "💌 Buzón Abierto", "🎧 Soundtrack y Planes"])

# ───────────── 1. Cielo ─────────────
with t1:
    st.markdown(f'<div class="dedic">{DEDICATORIA}</div>', unsafe_allow_html=True)
    hora = st.select_slider("Hora de esa noche (hora de Guadalajara)", options=[19, 20, 21, 22, 23],
                            value=21, format_func=lambda h: f"{h}:00")
    st.image(mapa_png(hora))
    st.caption("Vista hacia arriba: el centro es lo que tenías justo encima; el borde, el horizonte. "
               "Las estrellas se calculan con su posición real para esa fecha, lugar y hora.")

# ───────────── 2. Álbum ─────────────
with t2:
    fotos, pies = db.listar_fotos(), db.leer_json("album.json", {})
    if fotos:
        i = st.session_state.get("foto_i", 0) % len(fotos)
        st.image(db.bytes_foto(fotos[i]))
        st.markdown(f'<div class="pie">{html.escape(pies.get(fotos[i], ""))}</div>', unsafe_allow_html=True)
        a, b, c = st.columns([1, 2, 1])
        a.button("‹ Anterior", on_click=mover, args=(-1, len(fotos)), key="prev")
        b.markdown(f"<p style='text-align:center;margin-top:.5rem'>{i + 1} de {len(fotos)}</p>", unsafe_allow_html=True)
        c.button("Siguiente ›", on_click=mover, args=(1, len(fotos)), key="next")
    else:
        st.markdown('<div class="pie">Aquí van a vivir nuestros viajes. Sube la primera foto.</div>', unsafe_allow_html=True)

    with st.expander("📸 Subir fotos nuevas", expanded=not fotos):
        with st.form("subir", clear_on_submit=True):
            archivos = st.file_uploader("Elige fotos de tu galería o toma una",
                                        type=["jpg", "jpeg", "png", "webp", "heic"], accept_multiple_files=True)
            pie = st.text_input("Pie de foto (opcional)", placeholder="Ej. Ruta al Pacífico, 2024")
            guardar = st.form_submit_button("Guardar en el álbum")
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
            st.session_state.aviso = "Fotos guardadas en el álbum 💛"
            st.rerun()

# ───────────── 3. Buzón ─────────────
with t3:
    with st.form("nota", clear_on_submit=True):
        autor = st.radio("Escribe como", [YO, ELLA], horizontal=True)
        titulo = st.text_input("Título", placeholder="Para cuando me extrañes…")
        texto = st.text_area("Tu carta", height=260, placeholder="Escribe todo lo que quieras, sin prisa.")
        enviar = st.form_submit_button("Guardar en el buzón")
    if enviar and not texto.strip():
        st.warning("Escribe algo antes de guardar.")
    elif enviar:
        notas = db.leer_json("notas.json", [])
        notas.append({"autor": autor, "titulo": titulo.strip(), "texto": texto.strip(),
                      "fecha": f"{datetime.now(SIN):%d/%m/%Y %H:%M}"})
        db.guardar_json("notas.json", notas)
        st.session_state.aviso = "Carta guardada en el buzón 💌"
        st.rerun()

    notas = db.leer_json("notas.json", [])
    if not notas:
        st.markdown('<div class="pie">El buzón está vacío. Que la primera carta sea tuya.</div>', unsafe_allow_html=True)
    for k, n in enumerate(reversed(notas)):
        with st.expander(f"{n['titulo'] or 'Sin título'} · {n['autor']} · {n['fecha']}", expanded=(k == 0)):
            color = ORO if n["autor"] == YO else ROSA
            cuerpo = html.escape(n["texto"]).replace("\n", "<br>")
            st.markdown(f'<div class="nota" style="--c:{color}">{cuerpo}</div>', unsafe_allow_html=True)

# ───────────── 4. Soundtrack y planes ─────────────
with t4:
    if PLAYLIST_ID.startswith("TU_"):
        st.info("Pon el ID de su playlist en PLAYLIST_ID (en app.py) para ver el reproductor aquí.")
    else:
        components.html(
            f'<iframe style="border-radius:20px" src="https://open.spotify.com/embed/playlist/{PLAYLIST_ID}'
            f'?utm_source=generator&theme=0" width="100%" height="352" frameborder="0" '
            f'allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" '
            f'loading="lazy"></iframe>', height=360)

    st.markdown("### Planes por tachar")
    planes = db.leer_json("planes.json", SEMILLA_PLANES)

    def marcar(i):
        planes[i]["hecho"] = st.session_state[f"p_{planes[i]['id']}"]
        db.guardar_json("planes.json", planes)

    hechos = sum(p["hecho"] for p in planes)
    st.progress(hechos / len(planes) if planes else 0, text=f"{hechos} de {len(planes)} planes cumplidos")
    for i, p in enumerate(planes):
        clave = f"p_{p['id']}"
        st.session_state[clave] = p["hecho"]
        st.checkbox(f"~~{p['texto']}~~" if p["hecho"] else p["texto"], key=clave, on_change=marcar, args=(i,))

    with st.form("nuevo_plan", clear_on_submit=True):
        nuevo = st.text_input("Agregar un plan", placeholder="Ej. Ver amanecer en la playa")
        if st.form_submit_button("Agregar") and nuevo.strip():
            planes.append({"id": uuid.uuid4().hex[:8], "texto": nuevo.strip(), "hecho": False})
            db.guardar_json("planes.json", planes)
            st.rerun()
