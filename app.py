from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Sistema CN | Votorantim Cimentos",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed"
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


def app_link(path, label):
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
            max-width: 960px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}

        /* Remove informacoes repetidas da barra lateral */
        section[data-testid="stSidebar"] {{
            display: none;
        }}

        div[data-testid="collapsedControl"] {{
            display: none;
        }}

        header[data-testid="stHeader"] {{
            background: transparent;
        }}

        .vc-page {{
            display: flex;
            flex-direction: column;
            gap: 22px;
        }}

        .vc-logo-area {{
            background: #FFFFFF;
            border: 1px solid {VC_BORDER};
            border-radius: 20px;
            padding: 26px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            box-shadow: 0 10px 28px rgba(24, 68, 120, 0.07);
        }}

        .vc-logo-area img {{
            max-width: 245px;
            max-height: 70px;
            object-fit: contain;
        }}

        .vc-title {{
            text-align: right;
        }}

        .vc-title h1 {{
            margin: 0;
            color: {VC_BLUE};
            font-size: 30px;
            line-height: 1.1;
            font-weight: 900;
        }}

        .vc-title p {{
            margin: 6px 0 0 0;
            color: {VC_MUTED};
            font-size: 14px;
        }}

        .vc-menu-card {{
            background: #FFFFFF;
            border: 1px solid {VC_BORDER};
            border-radius: 22px;
            padding: 28px;
            box-shadow: 0 12px 32px rgba(24, 68, 120, 0.08);
        }}

        .vc-menu-card h2 {{
            margin: 0 0 4px 0;
            color: {VC_TEXT};
            font-size: 24px;
            font-weight: 900;
        }}

        .vc-menu-card p {{
            margin: 0 0 22px 0;
            color: {VC_MUTED};
            font-size: 14px;
        }}

        div[data-testid="stPageLink"] a {{
            background: #FFFFFF;
            border: 1px solid {VC_BORDER};
            border-left: 5px solid {VC_BLUE};
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 10px;
            color: {VC_BLUE};
            font-size: 16px;
            font-weight: 800;
            text-decoration: none;
            box-shadow: 0 6px 16px rgba(24, 68, 120, 0.05);
        }}

        div[data-testid="stPageLink"] a:hover {{
            border-color: {VC_LIGHT_BLUE};
            border-left-color: {VC_NAVY};
            box-shadow: 0 10px 24px rgba(24, 68, 120, 0.12);
            transform: translateY(-1px);
        }}

        .vc-footer {{
            text-align: center;
            color: {VC_MUTED};
            font-size: 12px;
            padding-top: 4px;
        }}

        @media (max-width: 760px) {{
            .vc-logo-area {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .vc-title {{
                text-align: left;
            }}

            .vc-title h1 {{
                font-size: 26px;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    f"""
    <div class="vc-page">
        <div class="vc-logo-area">
            <img src="{logo_src()}" alt="Votorantim Cimentos">
            <div class="vc-title">
                <h1>Sistema CN</h1>
                <p>Performance Industrial | Regional Centro-Norte</p>
            </div>
        </div>

        <div class="vc-menu-card">
            <h2>Portal de Indicadores Operacionais</h2>
            <p>Selecione uma pagina para acessar.</p>
    """,
    unsafe_allow_html=True
)

app_link("pages/1_Consolidacao.py", "Consolidacao")
app_link("pages/2_Dashboard_Consolidado.py", "Dashboard Consolidado")
app_link("pages/3_Dashboard_ST_FD.py", "Dashboard ST & FD")
app_link("pages/4_Metas.py", "Metas")

st.markdown(
    """
        </div>
        <div class="vc-footer">
            Votorantim Cimentos | Regional Centro-Norte
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
