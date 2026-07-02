"""
Balance de Puerto Tocopilla — Nitratos VSM
Herramienta interactiva en Streamlit.

Ejecutar:
    pip install streamlit
    streamlit run balance_puerto.py
"""

import json
from pathlib import Path
import streamlit as st

# ── Configuración de página ───────────────────────────────
st.set_page_config(page_title="Balance de Puerto", page_icon="⚓", layout="wide")

ESCENARIOS_FILE = Path("escenarios_balance.json")

# ── Datos base 2025 (borrador Sofía, hoja "Datos Gestion") ─
BASE_2025 = {
    "desdeCS": 683188,
    "embarque": 600901,
    "terrestre": 55163,
    "perdidaTransporte": 1164,
    "perdidaDescarga": 486,
    "devolucionCS": 3581,
    "mermas": 896,
    "degradacion": 1359,
    "deltaInventario": 12482,
    "castigo": 2790,
    "feRescatable": 4480,
    "precio": 627.9,
}
BASE_2026 = {**{k: 0 for k in BASE_2025}, "precio": 627.9, "feRescatable": 0}

# Salidas: (clave, etiqueta, fuente_por_confirmar)
SALIDAS = [
    ("embarque", "Embarque marítimo", False),
    ("terrestre", "Despacho terrestre", False),
    ("perdidaTransporte", "Pérdida transporte", False),
    ("perdidaDescarga", "Pérdida descarga", False),
    ("devolucionCS", "Devolución a CS", True),
    ("mermas", "Mermas", True),
    ("degradacion", "Degradación", True),
    ("deltaInventario", "Δ Inventario (final − inicial)", True),
    ("castigo", "Castigo recepción", True),
]

# ── Persistencia de escenarios ────────────────────────────
def cargar_escenarios():
    if ESCENARIOS_FILE.exists():
        try:
            return json.loads(ESCENARIOS_FILE.read_text())
        except Exception:
            return {}
    return {}

def guardar_escenario(nombre, datos):
    esc = cargar_escenarios()
    esc[nombre] = datos
    ESCENARIOS_FILE.write_text(json.dumps(esc, indent=2))

# ── Estilo ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #141a1f; }
    section[data-testid="stSidebar"] { background-color: #1c242b; }
    h1, h2, h3, p, label, span { color: #e8edf1 !important; }
    .eyebrow { color:#d9a441; font-size:12px; letter-spacing:2px;
               text-transform:uppercase; font-weight:600; }
</style>
""", unsafe_allow_html=True)

AMBER, TEAL, RED, MUTED = "#d9a441", "#4ec9a8", "#e0714f", "#8a99a6"

# ── Selección de escenario ────────────────────────────────
if "datos" not in st.session_state:
    st.session_state.datos = dict(BASE_2025)
    st.session_state.year = "2025"

st.markdown('<div class="eyebrow">Nitratos VSM · Puerto Tocopilla</div>', unsafe_allow_html=True)
st.title("Balance de Puerto")

esc_guardados = cargar_escenarios()

col_y1, col_y2, col_y3, _ = st.columns([1, 1, 1.4, 4])
with col_y1:
    if st.button("2025", use_container_width=True):
        st.session_state.datos = esc_guardados.get("2025", dict(BASE_2025))
        st.session_state.year = "2025"
with col_y2:
    if st.button("2026", use_container_width=True):
        st.session_state.datos = esc_guardados.get("2026", dict(BASE_2026))
        st.session_state.year = "2026"
with col_y3:
    if st.button(f"💾 Guardar {st.session_state.year}", use_container_width=True):
        guardar_escenario(st.session_state.year, st.session_state.datos)
        st.success(f"Escenario {st.session_state.year} guardado")

d = st.session_state.datos

# ── Sidebar: inputs ───────────────────────────────────────
with st.sidebar:
    st.subheader("Entrada")
    d["desdeCS"] = st.number_input("Ingreso desde Coya Sur (ton)",
                                   value=float(d["desdeCS"]), step=1000.0, format="%.0f")

    st.subheader("Salidas y pérdidas")
    st.caption("🟡 = fuente por confirmar con Danilo / Bárbara")
    for k, label, flag in SALIDAS:
        etiqueta = f"🟡 {label}" if flag else label
        d[k] = st.number_input(f"{etiqueta} (ton)", value=float(d[k]),
                               step=100.0, format="%.0f", key=f"in_{k}")

    st.subheader("Parámetros")
    d["feRescatable"] = st.number_input("Producto F/E rescatable (ton)",
                                        value=float(d["feRescatable"]), step=100.0, format="%.0f")
    d["precio"] = st.number_input("Precio / costo (USD/ton)",
                                  value=float(d["precio"]), step=1.0, format="%.1f")

# ── Cálculos ──────────────────────────────────────────────
salidas_total = sum(d[k] for k, _, _ in SALIDAS)
desbalance = d["desdeCS"] - salidas_total
cuadra = abs(desbalance) < 0.005 * (d["desdeCS"] or 1)

perdidas_ton = d["devolucionCS"] + d["mermas"] + d["degradacion"] + d["castigo"] + abs(desbalance)
efecto_musd = perdidas_ton * d["precio"] / 1e6
fe_valor_musd = d["feRescatable"] * d["precio"] / 1e6

f = lambda n: f"{n:,.0f}".replace(",", ".")
f1 = lambda n: f"{n:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ── Resultados ────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.markdown("#### Balance")
    st.metric("Entradas", f"{f(d['desdeCS'])} ton")
    st.metric("Salidas + pérdidas", f"{f(salidas_total)} ton")
    color = TEAL if cuadra else RED
    signo = "+" if desbalance > 0 else ""
    st.markdown(
        f"<div style='text-align:center;padding:14px;border:1px solid {color};border-radius:10px;'>"
        f"<div style='color:{MUTED};font-size:12px;letter-spacing:1.5px;text-transform:uppercase;'>"
        f"Desbalance (merma no explicada)</div>"
        f"<div style='font-size:42px;font-weight:700;color:{color};font-family:monospace;'>"
        f"{signo}{f(desbalance)}</div>"
        f"<div style='color:{color};font-weight:600;'>"
        f"{'✓ Balance cuadra (< 0,5%)' if cuadra else '▲ Requiere conciliación con puerto'}</div>"
        f"</div>", unsafe_allow_html=True)

with c2:
    st.markdown("#### Impacto económico de pérdidas")
    m1, m2 = st.columns(2)
    m1.metric("Ton en pérdidas", f(perdidas_ton))
    m2.metric("MUSD efecto", f1(efecto_musd))

    st.markdown(
        f"<div style='background:linear-gradient(135deg,#232d36,#1c242b);"
        f"border:1px solid {AMBER};border-radius:10px;padding:18px;margin-top:10px;'>"
        f"<div style='color:{AMBER};font-size:13px;font-weight:700;text-transform:uppercase;'>"
        f"Gestión F/E — valor recuperable</div>"
        f"<div style='color:{MUTED};font-size:12px;margin-bottom:8px;'>"
        f"Producto fuera de especificación que sí se puede rescatar</div>"
        f"<span style='font-size:34px;font-weight:700;color:{AMBER};font-family:monospace;'>{f1(fe_valor_musd)}</span>"
        f"<span style='color:{MUTED};'> MUSD &nbsp;·&nbsp; {f(d['feRescatable'])} ton</span>"
        f"</div>", unsafe_allow_html=True)

# ── Pendientes ────────────────────────────────────────────
st.markdown("#### Fuentes por confirmar")
pendientes = [label for _, label, flag in SALIDAS if flag]
st.markdown(
    " ".join(
        f"<span style='display:inline-block;font-size:13px;background:#141a1f;"
        f"border:1px solid {AMBER};color:{AMBER};border-radius:20px;"
        f"padding:4px 12px;margin:3px;'>{p}</span>"
        for p in pendientes
    ), unsafe_allow_html=True)

st.caption(
    "Prototipo · valores 2025 desde el borrador de Sofía (hoja «Datos Gestion»). "
    "Editá los campos en la barra lateral y el balance recalcula. "
    "Usá 2025 / 2026 y «Guardar» para conservar y comparar escenarios."
)
