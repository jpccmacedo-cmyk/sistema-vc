from pathlib import Path

import streamlit as st


# ============================================================
# Identidade visual padrão - Votorantim Cimentos / Regional CN
# ============================================================

VC_BLUE = "#184478"
VC_NAVY = "#0F218B"
VC_LIGHT_BLUE = "#7BBFE3"
VC_BG = "#F6F8FB"
VC_CARD = "#FFFFFF"
VC_TEXT = "#172033"
VC_MUTED = "#667085"
VC_BORDER = "#D9E2EC"
VC_GREEN = "#C6EFCE"
VC_YELLOW = "#FFE699"
VC_RED = "#FFC7CE"

LOGO_URL = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Logotipo_da_Votorantim_Cimentos.svg"
LOCAL_LOGO_PATHS = [
    "assets/votorantim_cimentos_logo.svg",
    "assets/votorantim_cimentos_logo.png",
    "assets/logo_votorantim.png",
    "assets/logo.png",
]


def logo_src():
    for logo_path in LOCAL_LOGO_PATHS:
        if Path(logo_path).exists():
            return logo_path
    return LOGO_URL


def configurar_pagina(titulo, icone=":bar_chart:", layout="wide"):
    st.set_page_config(
        page_title=titulo,
        page_icon=icone,
        layout=layout,
        initial_sidebar_state="expanded"
    )


def aplicar_css_global(max_width="100%", esconder_sidebar=False):
    sidebar_css = """
        section[data-testid='stSidebar'] {
            display: none;
        }
        div[data-testid='collapsedControl'] {
            display: none;
        }
    """ if esconder_sidebar else """
        section[data-testid='stSidebar'] {
            background: #FFFFFF;
            border-right: 1px solid #D9E2EC;
        }
    """

    st.markdown(
        f"""
        <style>
            .stApp {{
                background: {VC_BG};
                color: {VC_TEXT};
                font-family: Arial, Helvetica, sans-serif;
            }}

            .block-container {{
                max-width: {max_width} !important;
                padding-top: 1.2rem !important;
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
                padding-bottom: 2.4rem !important;
            }}

            header[data-testid="stHeader"] {{
                background: transparent;
            }}

            {sidebar_css}

            h1, h2, h3 {{
                color: {VC_TEXT};
                letter-spacing: -0.2px;
            }}

            div[data-testid="stMetric"] {{
                background: #FFFFFF;
                border: 1px solid {VC_BORDER};
                border-radius: 16px;
                padding: 14px 16px;
                box-shadow: 0 8px 22px rgba(24, 68, 120, 0.045);
            }}

            div[data-testid="stMetric"] label {{
                color: {VC_MUTED} !important;
            }}

            div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
                color: {VC_BLUE};
                font-weight: 800;
            }}

            div[data-testid="stTabs"] button {{
                font-size: 13px;
            }}

            div[data-testid="stPageLink"] a {{
                background: #FFFFFF;
                border: 1px solid {VC_BORDER};
                border-left: 5px solid {VC_BLUE};
                border-radius: 14px;
                padding: 14px 16px;
                color: {VC_BLUE};
                font-size: 15px;
                font-weight: 700;
                text-decoration: none;
                box-shadow: 0 6px 16px rgba(24, 68, 120, 0.05);
            }}

            div[data-testid="stPageLink"] a:hover {{
                border-color: {VC_LIGHT_BLUE};
                border-left-color: {VC_NAVY};
                box-shadow: 0 10px 24px rgba(24, 68, 120, 0.12);
                transform: translateY(-1px);
            }}

            .vc-page-header {{
                background: #FFFFFF;
                border: 1px solid {VC_BORDER};
                border-radius: 18px;
                padding: 18px 22px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 20px;
                box-shadow: 0 10px 28px rgba(24, 68, 120, 0.06);
                margin-bottom: 18px;
            }}

            .vc-page-header img {{
                max-width: 200px;
                max-height: 54px;
                object-fit: contain;
            }}

            .vc-page-header-title {{
                text-align: right;
            }}

            .vc-page-header-title h1 {{
                margin: 0;
                color: {VC_BLUE};
                font-size: 26px;
                line-height: 1.1;
                font-weight: 900;
            }}

            .vc-page-header-title p {{
                margin: 5px 0 0 0;
                color: {VC_MUTED};
                font-size: 13px;
            }}

            .vc-card {{
                background: #FFFFFF;
                border: 1px solid {VC_BORDER};
                border-radius: 18px;
                padding: 18px;
                box-shadow: 0 8px 22px rgba(24, 68, 120, 0.05);
            }}

            .vc-section-title {{
                font-size: 21px;
                font-weight: 900;
                color: {VC_TEXT};
                margin: 10px 0 12px 0;
            }}

            .vc-small-muted {{
                color: {VC_MUTED};
                font-size: 13px;
            }}

            .vc-footer {{
                text-align: center;
                color: {VC_MUTED};
                font-size: 12px;
                margin-top: 24px;
            }}

            @media (max-width: 760px) {{
                .vc-page-header {{
                    flex-direction: column;
                    align-items: flex-start;
                }}

                .vc-page-header-title {{
                    text-align: left;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True
    )


def render_header(titulo, subtitulo="Performance Industrial | Regional Centro-Norte", mostrar_logo=True):
    logo = f"<img src='{logo_src()}' alt='Votorantim Cimentos'>" if mostrar_logo else ""
    st.markdown(
        f"""
        <div class="vc-page-header">
            <div>{logo}</div>
            <div class="vc-page-header-title">
                <h1>{titulo}</h1>
                <p>{subtitulo}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_footer():
    st.markdown(
        """
        <div class="vc-footer">
            Votorantim Cimentos | Regional Centro-Norte
        </div>
        """,
        unsafe_allow_html=True
    )


def render_sidebar_logo(texto="Regional Centro-Norte"):
    st.sidebar.image(logo_src(), width=190)
    st.sidebar.caption(texto)
    st.sidebar.markdown("---")


def section_title(texto):
    st.markdown(f"<div class='vc-section-title'>{texto}</div>", unsafe_allow_html=True)


def info_card(html):
    st.markdown(f"<div class='vc-card'>{html}</div>", unsafe_allow_html=True)
