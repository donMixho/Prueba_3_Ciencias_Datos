"""Infraestructura de estilo del dashboard (paleta, CSS, componentes UI).

Centraliza la identidad visual para que todas las vistas luzcan consistentes y
profesionales. Uso típico en cada página:

    from theme import setup_page, page_header, kpi_card, style_fig, footer
    setup_page("Ejecutiva", "📊")
    page_header("Vista Ejecutiva", "Indicadores clave de salud poblacional")
"""

from __future__ import annotations

import plotly.express as px
import plotly.io as pio
import streamlit as st

# --------------------------------------------------------------------------- #
# Paleta de marca
# --------------------------------------------------------------------------- #
PRIMARY = "#0E7490"      # cyan-700
PRIMARY_DARK = "#155E75"  # cyan-800
ACCENT = "#0891B2"       # cyan-600
INK = "#0F172A"          # slate-900
MUTED = "#64748B"        # slate-500
SURFACE = "#F8FAFC"      # slate-50

# Secuencia de colores para series (coherente y legible)
SEQ = ["#0E7490", "#0891B2", "#F59E0B", "#EF4444", "#10B981", "#6366F1"]
# Colores semánticos de riesgo
RISK = {"low": "#10B981", "mid": "#F59E0B", "high": "#EF4444"}


# --------------------------------------------------------------------------- #
# Plantilla Plotly profesional
# --------------------------------------------------------------------------- #
def _register_plotly_template() -> None:
    tmpl = pio.templates["plotly_white"]
    tmpl.layout.font.update(family="Inter, Segoe UI, sans-serif", color=INK, size=13)
    tmpl.layout.colorway = SEQ
    tmpl.layout.title.update(font=dict(size=18, color=INK))
    tmpl.layout.margin = dict(l=10, r=10, t=50, b=10)
    tmpl.layout.hovermode = "x unified"
    tmpl.layout.legend.update(orientation="h", yanchor="bottom", y=1.02, x=0)
    pio.templates["nhanes"] = tmpl
    pio.templates.default = "nhanes"
    px.defaults.template = "nhanes"
    px.defaults.color_discrete_sequence = SEQ


def style_fig(fig, height: int | None = None):
    """Aplica el estilo de marca a una figura Plotly."""
    fig.update_layout(
        template="nhanes",
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E2E8F0")
    return fig


# --------------------------------------------------------------------------- #
# CSS global
# --------------------------------------------------------------------------- #
_CSS = f"""
<style>
    /* Tipografía y fondo general */
    html, body, [class*="css"] {{ font-family: 'Inter','Segoe UI',sans-serif; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1300px; }}

    /* Header / hero */
    .hero {{
        background: linear-gradient(120deg, {PRIMARY_DARK} 0%, {PRIMARY} 60%, {ACCENT} 100%);
        color: #fff; padding: 1.6rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(14,116,144,0.18);
    }}
    .hero h1 {{ margin: 0; font-size: 1.7rem; font-weight: 700; color:#fff; }}
    .hero p  {{ margin: .35rem 0 0; opacity: .92; font-size: 1rem; }}
    .hero .badge {{
        display:inline-block; margin-top:.8rem; background: rgba(255,255,255,.18);
        padding:.25rem .7rem; border-radius:999px; font-size:.8rem; font-weight:600;
    }}

    /* KPI cards */
    .kpi {{
        background:#fff; border:1px solid #E2E8F0; border-radius:14px;
        padding:1.1rem 1.2rem; box-shadow:0 1px 3px rgba(15,23,42,.06);
        border-left:5px solid {PRIMARY}; height:100%;
    }}
    .kpi .icon {{ font-size:1.4rem; }}
    .kpi .value {{ font-size:2rem; font-weight:700; color:{INK}; line-height:1.1; }}
    .kpi .label {{ font-size:.85rem; color:{MUTED}; font-weight:600; text-transform:uppercase; letter-spacing:.03em; }}

    /* Section titles */
    .section {{ font-size:1.15rem; font-weight:700; color:{INK};
        border-left:4px solid {PRIMARY}; padding-left:.6rem; margin:.4rem 0 1rem; }}

    /* Footer */
    .footer {{ color:{MUTED}; font-size:.8rem; text-align:center;
        border-top:1px solid #E2E8F0; padding-top:1rem; margin-top:2.5rem; }}

    /* Tablas más limpias */
    [data-testid="stDataFrame"] {{ border:1px solid #E2E8F0; border-radius:12px; }}

    /* Oculta el menú/footer por defecto de Streamlit para un look de producto */
    #MainMenu {{ visibility:hidden; }}
    footer {{ visibility:hidden; }}
</style>
"""


# --------------------------------------------------------------------------- #
# Componentes de alto nivel
# --------------------------------------------------------------------------- #
def setup_page(title: str, icon: str = "🩺") -> None:
    """Configura la página e inyecta el tema. Llamar al inicio de cada vista."""
    st.set_page_config(page_title=f"NHANES · {title}", page_icon=icon, layout="wide")
    _register_plotly_template()
    st.markdown(_CSS, unsafe_allow_html=True)
    _sidebar_brand()


def _sidebar_brand() -> None:
    with st.sidebar:
        st.markdown(
            f"<div style='font-weight:800;font-size:1.1rem;color:{PRIMARY_DARK}'>🩺 NHANES</div>"
            f"<div style='color:{MUTED};font-size:.8rem;margin-bottom:.5rem'>Riesgo Cardiometabólico</div>",
            unsafe_allow_html=True,
        )
        st.caption("Datos: CDC · NHANES 2017-2018")


def page_header(title: str, subtitle: str = "", badge: str = "NHANES 2017-2018 · CDC") -> None:
    st.markdown(
        f"""<div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <span class="badge">📡 {badge}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def kpi_card(col, label: str, value: str, icon: str = "📊", accent: str = PRIMARY) -> None:
    """Renderiza una tarjeta KPI estilizada dentro de una columna."""
    col.markdown(
        f"""<div class="kpi" style="border-left-color:{accent}">
            <div class="icon">{icon}</div>
            <div class="value">{value}</div>
            <div class="label">{label}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="section">{title}</div>', unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        '<div class="footer">Plataforma de Análisis Cardiometabólico · '
        "ETL (Kedro) → API (FastAPI) → Dashboard (Streamlit) · "
        "Fuente: CDC NHANES 2017-2018</div>",
        unsafe_allow_html=True,
    )
