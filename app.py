from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Sistema CN | Votorantim Cimentos",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)


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


def logo_src():
    for logo_path in LOCAL_LOGO_PATHS:
        if Path(logo_path).exists():
            return logo_path
    return LOGO_URL


def page_exists(path):
    return Path(path).exists()


def safe_page_button(path, label):
    if page_exists(path):
        st.page_link(path, label=label)
    else:
        st.caption("Pagina nao encontrada: " + path)


st.markdown(
    f"""
    <style>
        .stApp {{
            background: {VC_BG};
            color: {VC_TEXT};
        }}

        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1120px;
        }}

        section[data-testid="stSidebar"] {{
            background: #FFFFFF;
            border-right: 1px solid {VC_BORDER};
        }}

        div[data-testid="stPageLink"] a {{
            background: #FFFFFF;
            border: 1px solid {VC_BORDER};
            border-radius: 12px;
            padding: 11px 13px;
            text-decoration: none;
            font-size: 14px;
            color: {VC_BLUE};
        }}

        div[data-testid="stPageLink"] a:hover {{
            border-color: {VC_LIGHT_BLUE};
            box-shadow: 0 6px 16px rgba(24, 68, 120, 0.10);
        }}

        .vc-header {{
            background: #FFFFFF;
            border: 1px solid {VC_BORDER};
            border-radius: 18px;
            padding: 18px 22px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            box-shadow: 0 8px 22px rgba(24, 68, 120, 0.06);
            margin-bottom: 18px;
        }}

        .vc-header img {{
            max-width: 210px;
            max-height: 58px;
            object-fit: contain;
        }}

        .vc-header-title {{
            text-align: right;
        }}

        .vc-header-title h1 {{
            margin: 0;
            color: {VC_BLUE};
            font-size: 26px;
            font-weight: 900;
            line-height: 1.1;
        }}

        .vc-header-title span {{
            display: block;
            margin-top: 4px;
            color: {VC_MUTED};
            font-size: 13px;
        }}

        .vc-hero {{
            background: linear-gradient(135deg, {VC_BLUE}, {VC_NAVY});
            color: #FFFFFF;
            border-radius: 20px;
            padding: 28px 32px;
            box-shadow: 0 16px 38px rgba(24, 68, 120, 0.18);
            margin-bottom: 22px;
        }}

        .vc-hero h2 {{
            margin: 0;
            color: #FFFFFF;
            font-size: 32px;
            font-weight: 900;
            letter-spacing: -0.3px;
        }}

        .vc-hero p {{
            margin: 8px 0 0 0;
            color: rgba(255,255,255,0.86);
            font-size: 15px;
            line-height: 1.5;
        }}

        .vc-section-title {{
            font-size: 20px;
            font-weight: 900;
            color: {VC_TEXT};
            margin: 6px 0 10px 0;
        }}

        .vc-card-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin-top: 14px;
        }}

        .vc-card {{
            background: {VC_CARD};
            border: 1px solid {VC_BORDER};
            border-radius: 18px;
            padding: 20px 18px;
            box-shadow: 0 8px 20px rgba(24, 68, 120, 0.05);
            min-height: 84px;
            display: flex;
            align-items: center;
        }}

        .vc-card h3 {{
            margin: 0;
            color: {VC_BLUE};
            font-size: 17px;
            font-weight: 900;
        }}

        .vc-footer {{
            margin-top: 28px;
            text-align: center;
            color: {VC_MUTED};
            font-size: 12px;
        }}

        @media (max-width: 950px) {{
            .vc-card-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .vc-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .vc-header-title {{
                text-align: left;
            }}
        }}

        @media (max-width: 620px) {{
            .vc-card-grid {{
                grid-template-columns: 1fr;
            }}
            .vc-hero h2 {{
                font-size: 26px;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True
)


# Sidebar
st.sidebar.image(logo_src(), width=190)
st.sidebar.markdown("### Navegacao")
safe_page_button("pages/1_Consolidacao.py", "Consolidacao")
safe_page_button("pages/2_Dashboard_Consolidado.py", "Dashboard Consolidado")
safe_page_button("pages/3_Dashboard_ST_FD.py", "Dashboard ST & FD")
safe_page_button("pages/4_Metas.py", "Metas")
st.sidebar.markdown("---")
st.sidebar.caption("Votorantim Cimentos | Regional CN")


# Header
st.markdown(
    f"""
    <div class="vc-header">
        <img src="{logo_src()}" alt="Votorantim Cimentos">
        <div class="vc-header-title">
            <h1>Sistema CN</h1>
            <span>Performance Industrial | Regional Centro-Norte</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# Hero
st.markdown(
    """
    <div class="vc-hero">
        <h2>Portal de Indicadores Operacionais</h2>
        <p>Consolidado mensal, Farol de metas, ST Heatmap e FD Multiflex.</p>
    </div>
    """,
    unsafe_allow_html=True
)


# Links
st.markdown("<div class='vc-section-title'>Acesso rapido</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    safe_page_button("pages/1_Consolidacao.py", "Abrir Consolidacao")

with col2:
    safe_page_button("pages/2_Dashboard_Consolidado.py", "Abrir Dashboard Consolidado")

with col3:
    safe_page_button("pages/3_Dashboard_ST_FD.py", "Abrir ST & FD")

with col4:
    safe_page_button("pages/4_Metas.py", "Abrir Metas")


# Cards simples, sem descricoes
st.markdown(
    """
    <div class="vc-card-grid">
        <div class="vc-card"><h3>Consolidacao</h3></div>
        <div class="vc-card"><h3>Dashboard Consolidado</h3></div>
        <div class="vc-card"><h3>ST & FD</h3></div>
        <div class="vc-card"><h3>Metas</h3></div>
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
