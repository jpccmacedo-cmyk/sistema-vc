from pathlib import Path
from datetime import datetime

import streamlit as st


st.set_page_config(
    page_title="Sistema CN | Votorantim Cimentos",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# Identidade visual
# ============================================================

LOGO_URL = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Logotipo_da_Votorantim_Cimentos.svg"
LOCAL_LOGO_PATHS = [
    "assets/votorantim_cimentos_logo.svg",
    "assets/votorantim_cimentos_logo.png",
    "assets/logo_votorantim.png",
    "assets/logo.png",
]

VC_BLUE = "#184478"
VC_NAVY = "#0F218B"
VC_LIGHT_BLUE = "#7BBFE3"
VC_BG = "#F6F8FB"
VC_CARD = "#FFFFFF"
VC_TEXT = "#172033"
VC_MUTED = "#667085"
VC_BORDER = "#D9E2EC"


# ============================================================
# Funcoes auxiliares
# ============================================================

def logo_html():
    for logo_path in LOCAL_LOGO_PATHS:
        if Path(logo_path).exists():
            return f"<img src='{logo_path}' alt='Votorantim Cimentos'>"
    return f"<img src='{LOGO_URL}' alt='Votorantim Cimentos'>"


def page_exists(path):
    return Path(path).exists()


def safe_page_link(path, label):
    if page_exists(path):
        st.page_link(path, label=label)
    else:
        st.caption("Pagina nao encontrada: " + path)


def saudacao():
    hora = datetime.now().hour
    if hora < 12:
        return "Bom dia"
    if hora < 18:
        return "Boa tarde"
    return "Boa noite"


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>
        .stApp {{
            background: {VC_BG};
            color: {VC_TEXT};
        }}

        .block-container {{
            padding-top: 1.3rem;
            padding-bottom: 2.5rem;
            max-width: 1180px;
        }}

        section[data-testid="stSidebar"] {{
            background: #FFFFFF;
            border-right: 1px solid {VC_BORDER};
        }}

        div[data-testid="stPageLink"] a {{
            border-radius: 12px;
            border: 1px solid {VC_BORDER};
            background: #FFFFFF;
            padding: 10px 12px;
            font-size: 14px;
            text-decoration: none;
        }}

        div[data-testid="stPageLink"] a:hover {{
            border-color: {VC_LIGHT_BLUE};
            box-shadow: 0 6px 18px rgba(24, 68, 120, 0.10);
        }}

        .vc-shell {{
            display: flex;
            flex-direction: column;
            gap: 18px;
        }}

        .vc-header {{
            background: #FFFFFF;
            border: 1px solid {VC_BORDER};
            border-radius: 18px;
            padding: 18px 22px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 8px 24px rgba(24, 68, 120, 0.06);
        }}

        .vc-logo img {{
            max-width: 205px;
            max-height: 54px;
            object-fit: contain;
        }}

        .vc-header-text {{
            text-align: right;
        }}

        .vc-header-text .system {{
            font-size: 24px;
            font-weight: 900;
            color: {VC_BLUE};
            line-height: 1.1;
        }}

        .vc-header-text .region {{
            font-size: 13px;
            color: {VC_MUTED};
            margin-top: 4px;
        }}

        .vc-hero {{
            border-radius: 22px;
            padding: 30px 34px;
            background: linear-gradient(135deg, {VC_BLUE} 0%, {VC_NAVY} 100%);
            box-shadow: 0 16px 40px rgba(24, 68, 120, 0.18);
            color: #FFFFFF;
        }}

        .vc-hero .eyebrow {{
            font-size: 13px;
            font-weight: 700;
            color: rgba(255,255,255,0.78);
            margin-bottom: 8px;
        }}

        .vc-hero h1 {{
            margin: 0;
            font-size: 34px;
            line-height: 1.12;
            font-weight: 900;
            color: #FFFFFF;
            letter-spacing: -0.4px;
        }}

        .vc-hero p {{
            margin: 10px 0 0 0;
            max-width: 760px;
            color: rgba(255,255,255,0.86);
            font-size: 15px;
            line-height: 1.55;
        }}

        .vc-title-row {{
            margin-top: 8px;
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 14px;
        }}

        .vc-title-row h2 {{
            margin: 0;
            font-size: 21px;
            color: {VC_TEXT};
            font-weight: 900;
        }}

        .vc-title-row span {{
            color: {VC_MUTED};
            font-size: 13px;
        }}

        .vc-card-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
        }}

        .vc-card {{
            background: {VC_CARD};
            border: 1px solid {VC_BORDER};
            border-radius: 18px;
            padding: 18px;
            min-height: 128px;
            box-shadow: 0 8px 22px rgba(24, 68, 120, 0.055);
        }}

        .vc-card .tag {{
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            background: #EFF7FC;
            color: {VC_BLUE};
            border: 1px solid #D9EAF5;
            font-size: 11px;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .vc-card h3 {{
            margin: 0 0 7px 0;
            color: {VC_BLUE};
            font-size: 16px;
            font-weight: 900;
        }}

        .vc-card p {{
            margin: 0;
            color: {VC_MUTED};
            font-size: 13px;
            line-height: 1.45;
        }}

        .vc-info {{
            background: #FFFFFF;
            border: 1px solid {VC_BORDER};
            border-radius: 18px;
            padding: 16px 18px;
            color: {VC_MUTED};
            font-size: 13px;
            line-height: 1.5;
        }}

        .vc-footer {{
            text-align: center;
            color: {VC_MUTED};
            font-size: 12px;
            margin-top: 10px;
            padding: 8px;
        }}

        @media (max-width: 1000px) {{
            .vc-card-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .vc-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .vc-header-text {{
                text-align: left;
            }}
        }}

        @media (max-width: 650px) {{
            .vc-card-grid {{
                grid-template-columns: 1fr;
            }}
            .vc-hero h1 {{
                font-size: 28px;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# Sidebar
# ============================================================

st.sidebar.markdown(
    f"""
    <div style="padding: 10px 0 18px 0;">
        <div style="width:190px; margin-bottom:10px;">
            {logo_html()}
        </div>
        <div style="font-size:13px;color:{VC_MUTED};line-height:1.45;">
            Portal de indicadores<br>Regional Centro-Norte
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("### Navegacao")
safe_page_link("pages/1_Consolidacao.py", "Consolidacao")
safe_page_link("pages/2_Dashboard_Consolidado.py", "Dashboard Consolidado")
safe_page_link("pages/3_Dashboard_ST_FD.py", "Dashboard ST & FD")
safe_page_link("pages/4_Metas.py", "Metas")
st.sidebar.markdown("---")
st.sidebar.caption("Votorantim Cimentos")


# ============================================================
# Conteudo principal
# ============================================================

st.markdown(
    f"""
    <div class="vc-shell">
        <div class="vc-header">
            <div class="vc-logo">{logo_html()}</div>
            <div class="vc-header-text">
                <div class="system">Sistema CN</div>
                <div class="region">Performance Industrial | Votorantim Cimentos</div>
            </div>
        </div>

        <section class="vc-hero">
            <div class="eyebrow">{saudacao()}, Regional CN</div>
            <h1>Portal de Indicadores Operacionais</h1>
            <p>
                Consulte os dashboards de consolidacao, metas, farol mensal, ST Heatmap e FD Multiflex em um ambiente unico e padronizado.
            </p>
        </section>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="vc-title-row">
        <h2>Acesso rapido</h2>
        <span>Selecione uma pagina para continuar</span>
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    safe_page_link("pages/1_Consolidacao.py", "Abrir Consolidacao")

with col2:
    safe_page_link("pages/2_Dashboard_Consolidado.py", "Abrir Dashboard Consolidado")

with col3:
    safe_page_link("pages/3_Dashboard_ST_FD.py", "Abrir ST & FD")

with col4:
    safe_page_link("pages/4_Metas.py", "Abrir Metas")

st.markdown(
    """
    <div class="vc-card-grid">
        <div class="vc-card">
            <span class="tag">Entrada</span>
            <h3>Consolidacao</h3>
            <p>Upload e processamento dos arquivos mensais.</p>
        </div>
        <div class="vc-card">
            <span class="tag">Mensal</span>
            <h3>Dashboard Consolidado</h3>
            <p>Farol MTD, metas, status por planta e historico.</p>
        </div>
        <div class="vc-card">
            <span class="tag">Diario</span>
            <h3>ST & FD</h3>
            <p>Heatmaps operacionais com exportacao em PNG e HTML.</p>
        </div>
        <div class="vc-card">
            <span class="tag">Admin</span>
            <h3>Metas</h3>
            <p>Cadastro e manutencao das metas utilizadas no farol.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="vc-info">
        Este portal centraliza a consulta dos indicadores da Regional CN. Para preservar a governanca dos dados, recomenda-se restringir Metas e exclusoes ao administrador.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="vc-footer">
        Votorantim Cimentos | Regional Centro-Norte
    </div>
    """,
    unsafe_allow_html=True
)
