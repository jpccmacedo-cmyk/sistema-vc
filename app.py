from pathlib import Path
import base64
import mimetypes

import streamlit as st


st.set_page_config(
    page_title="Sistema CN | Votorantim Cimentos",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# Configurações de marca
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
VC_SOFT_BLUE = "#EFF7FC"


# ============================================================
# Funções auxiliares
# ============================================================

def logo_src():
    """Usa logo local quando existir; caso contrário, usa URL pública."""
    for logo_path in LOCAL_LOGO_PATHS:
        path = Path(logo_path)
        if path.exists():
            mime = mimetypes.guess_type(path.name)[0] or "image/png"
            encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
            return f"data:{mime};base64,{encoded}"
    return LOGO_URL


def page_exists(path):
    return Path(path).exists()


def menu_link(path, label, description=""):
    if page_exists(path):
        st.page_link(path, label=label)
        if description:
            st.markdown(f"<div class='vc-link-hint'>{description}</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            f"""
            <div class="vc-missing-link">
                Página não encontrada: <b>{path}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# CSS global
# ============================================================

st.markdown(
    f"""
    <style>
        :root {{
            --vc-blue: {VC_BLUE};
            --vc-navy: {VC_NAVY};
            --vc-light-blue: {VC_LIGHT_BLUE};
            --vc-bg: {VC_BG};
            --vc-card: {VC_CARD};
            --vc-text: {VC_TEXT};
            --vc-muted: {VC_MUTED};
            --vc-border: {VC_BORDER};
            --vc-soft-blue: {VC_SOFT_BLUE};
        }}

        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(123, 191, 227, 0.22), transparent 32%),
                linear-gradient(180deg, #F9FBFE 0%, var(--vc-bg) 48%, #EEF4FA 100%);
            color: var(--vc-text);
        }}

        .block-container {{
            max-width: 980px !important;
            padding-top: 0 !important;
            padding-bottom: 2.4rem !important;
        }}

        header[data-testid="stHeader"] {{
            background: transparent;
            height: 0rem;
        }}

        section[data-testid="stSidebar"] {{
            display: none;
        }}

        div[data-testid="collapsedControl"] {{
            display: none;
        }}

        /* Espaço reservado para o header fixo não cobrir o conteúdo */
        .vc-fixed-spacer {{
            height: 104px;
        }}

        /* Header realmente fixo na viewport durante a rolagem */
        .vc-fixed-header-outer {{
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            width: min(980px, calc(100vw - 32px));
            z-index: 999999;
            pointer-events: none;
        }}

        .vc-fixed-header {{
            pointer-events: auto;
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid rgba(217, 226, 236, 0.95);
            border-radius: 22px;
            padding: 15px 20px;
            box-shadow: 0 16px 42px rgba(24, 68, 120, 0.14);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
        }}

        .vc-header-content {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 22px;
        }}

        .vc-brand-area {{
            display: flex;
            align-items: center;
            gap: 18px;
            min-width: 0;
        }}

        .vc-logo-box {{
            display: flex;
            align-items: center;
            justify-content: flex-start;
            min-width: 205px;
            max-width: 245px;
            height: 56px;
        }}

        .vc-logo-box img {{
            max-width: 220px;
            max-height: 54px;
            object-fit: contain;
        }}

        .vc-title-block {{
            border-left: 1px solid var(--vc-border);
            padding-left: 18px;
        }}

        .vc-title-block h1 {{
            margin: 0;
            color: var(--vc-blue);
            font-size: 26px;
            line-height: 1.05;
            font-weight: 900;
            letter-spacing: -0.4px;
        }}

        .vc-title-block p {{
            margin: 6px 0 0 0;
            color: var(--vc-muted);
            font-size: 13px;
            line-height: 1.35;
        }}

        .vc-header-chip {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--vc-soft-blue);
            border: 1px solid #D8EAF6;
            color: #274263;
            border-radius: 999px;
            padding: 9px 13px;
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
        }}

        .vc-header-chip-dot {{
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--vc-light-blue);
            display: inline-block;
        }}

        .vc-hero {{
            background: linear-gradient(135deg, var(--vc-blue) 0%, var(--vc-navy) 100%);
            color: #FFFFFF;
            border-radius: 24px;
            padding: 34px 36px;
            box-shadow: 0 18px 46px rgba(24, 68, 120, 0.22);
            margin-bottom: 18px;
            overflow: hidden;
            position: relative;
        }}

        .vc-hero::after {{
            content: "";
            position: absolute;
            right: -70px;
            top: -70px;
            width: 210px;
            height: 210px;
            border-radius: 999px;
            background: rgba(123, 191, 227, 0.22);
        }}

        .vc-hero h2 {{
            margin: 0;
            color: #FFFFFF;
            font-size: 34px;
            line-height: 1.12;
            font-weight: 900;
            letter-spacing: -0.6px;
            position: relative;
            z-index: 2;
        }}

        .vc-hero p {{
            margin: 10px 0 0 0;
            max-width: 680px;
            color: rgba(255,255,255,0.88);
            font-size: 15px;
            line-height: 1.55;
            position: relative;
            z-index: 2;
        }}

        .vc-menu-card {{
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 24px;
            padding: 26px 28px 24px 28px;
            box-shadow: 0 12px 32px rgba(24, 68, 120, 0.075);
        }}

        .vc-menu-title {{
            display: flex;
            justify-content: space-between;
            align-items: end;
            gap: 14px;
            margin-bottom: 18px;
        }}

        .vc-menu-title h3 {{
            margin: 0;
            color: var(--vc-text);
            font-size: 23px;
            font-weight: 900;
            letter-spacing: -0.3px;
        }}

        .vc-menu-title span {{
            color: var(--vc-muted);
            font-size: 13px;
            white-space: nowrap;
        }}

        div[data-testid="stPageLink"] {{
            margin-bottom: 10px;
        }}

        div[data-testid="stPageLink"] a {{
            background: #FFFFFF;
            border: 1px solid var(--vc-border);
            border-left: 5px solid var(--vc-blue);
            border-radius: 16px;
            padding: 16px 18px;
            color: var(--vc-blue);
            font-size: 16px;
            font-weight: 850;
            text-decoration: none;
            box-shadow: 0 7px 18px rgba(24, 68, 120, 0.055);
            transition: all .16s ease;
        }}

        div[data-testid="stPageLink"] a:hover {{
            border-color: var(--vc-light-blue);
            border-left-color: var(--vc-navy);
            box-shadow: 0 12px 26px rgba(24, 68, 120, 0.13);
            transform: translateY(-1px);
        }}

        .vc-link-hint {{
            margin: -6px 0 12px 23px;
            color: var(--vc-muted);
            font-size: 12px;
        }}

        .vc-missing-link {{
            padding: 14px 16px;
            border: 1px dashed #CBD5E1;
            background: #FFFFFF;
            border-radius: 14px;
            color: var(--vc-muted);
            font-size: 13px;
            margin-bottom: 10px;
        }}

        .vc-footer {{
            text-align: center;
            color: var(--vc-muted);
            font-size: 12px;
            margin-top: 24px;
            padding: 8px;
        }}

        @media (max-width: 760px) {{
            .vc-fixed-spacer {{
                height: 166px;
            }}

            .vc-fixed-header-outer {{
                top: 8px;
                width: calc(100vw - 22px);
            }}

            .vc-header-content {{
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }}

            .vc-brand-area {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}

            .vc-title-block {{
                border-left: 0;
                padding-left: 0;
            }}

            .vc-logo-box {{
                min-width: unset;
                height: auto;
            }}

            .vc-hero {{
                padding: 28px 24px;
            }}

            .vc-hero h2 {{
                font-size: 28px;
            }}

            .vc-menu-title {{
                flex-direction: column;
                align-items: flex-start;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Cabeçalho fixo
# ============================================================

st.markdown(
    f"""
    <div class="vc-fixed-header-outer">
        <div class="vc-fixed-header">
            <div class="vc-header-content">
                <div class="vc-brand-area">
                    <div class="vc-logo-box">
                        <img src="{logo_src()}" alt="Votorantim Cimentos">
                    </div>
                    <div class="vc-title-block">
                        <h1>Sistema CN</h1>
                        <p>Performance Industrial | Regional Centro-Norte</p>
                    </div>
                </div>
                <div class="vc-header-chip">
                    <span class="vc-header-chip-dot"></span>
                    Portal de Indicadores
                </div>
            </div>
        </div>
    </div>
    <div class="vc-fixed-spacer"></div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Conteúdo principal
# ============================================================

st.markdown(
    """
    <section class="vc-hero">
        <h2>Gestão operacional em um único ambiente</h2>
        <p>
            Acesse os módulos da Regional CN para consolidação, farol mensal, ST Heatmap, FD Multiflex e gestão de metas.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="vc-menu-card">
        <div class="vc-menu-title">
            <h3>Páginas do sistema</h3>
            <span>Selecione uma opção</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

menu_link("pages/1_Consolidacao.py", "Consolidação", "Processamento dos arquivos mensais.")
menu_link("pages/2_Dashboard_Consolidado.py", "Dashboard Consolidado", "Farol mensal, metas e histórico consolidado.")
menu_link("pages/3_Dashboard_ST_FD.py", "Dashboard ST & FD", "Heatmaps de ST e FD Multiflex.")
menu_link("pages/4_Metas.py", "Metas", "Cadastro e manutenção das metas do sistema.")

st.markdown(
    """
    <div class="vc-footer">
        Votorantim Cimentos | Regional Centro-Norte
    </div>
    """,
    unsafe_allow_html=True,
)
