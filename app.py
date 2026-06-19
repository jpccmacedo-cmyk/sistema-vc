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
VC_LIGHT_BLUE = "#7BBFE3"
VC_BG = "#F5F8FC"
VC_BORDER = "#D8E2EE"
VC_TEXT = "#0F172A"
VC_MUTED = "#64748B"


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


st.markdown(
    f"""
    <style>
        .stApp {{
            background: {VC_BG};
            color: {VC_TEXT};
        }}

        section[data-testid="stSidebar"] {{
            background: #FFFFFF;
            border-right: 1px solid {VC_BORDER};
        }}

        .block-container {{
            padding-top: 1.4rem;
            max-width: 1180px;
        }}

        .vc-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            background: #FFFFFF;
            border: 1px solid {VC_BORDER};
            border-radius: 18px;
            padding: 18px 22px;
            margin-bottom: 22px;
            box-shadow: 0 8px 24px rgba(24, 68, 120, 0.08);
        }}

        .vc-logo img {{
            max-width: 210px;
            max-height: 58px;
            object-fit: contain;
        }}

        .vc-title {{
            text-align: right;
        }}

        .vc-title h1 {{
            color: {VC_BLUE};
            font-size: 28px;
            margin: 0;
            font-weight: 900;
        }}

        .vc-title p {{
            margin: 4px 0 0 0;
            color: {VC_MUTED};
            font-size: 14px;
        }}

        .vc-hero {{
            background: linear-gradient(135deg, {VC_BLUE}, #0F218B);
            color: #FFFFFF;
            border-radius: 22px;
            padding: 30px 34px;
            margin-bottom: 24px;
            box-shadow: 0 18px 44px rgba(24, 68, 120, 0.18);
        }}

        .vc-hero h2 {{
            color: #FFFFFF;
            font-size: 34px;
            margin: 0 0 8px 0;
            font-weight: 900;
        }}

        .vc-hero p {{
            color: rgba(255,255,255,0.88);
            font-size: 15px;
            margin: 0;
            max-width: 760px;
            line-height: 1.5;
        }}

        .vc-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 16px;
            margin-top: 14px;
        }}

        .vc-card {{
            background: #FFFFFF;
            border: 1px solid {VC_BORDER};
            border-radius: 18px;
            padding: 18px;
            min-height: 118px;
            box-shadow: 0 8px 22px rgba(24, 68, 120, 0.06);
        }}

        .vc-card h3 {{
            margin: 0 0 8px 0;
            color: {VC_BLUE};
            font-size: 17px;
            font-weight: 900;
        }}

        .vc-card p {{
            margin: 0;
            color: {VC_MUTED};
            font-size: 13px;
            line-height: 1.45;
        }}

        .vc-section-title {{
            color: {VC_TEXT};
            font-size: 22px;
            font-weight: 900;
            margin: 10px 0 8px 0;
        }}

        .vc-footer {{
            text-align: center;
            color: {VC_MUTED};
            font-size: 12px;
            margin-top: 32px;
            padding: 14px;
        }}

        @media (max-width: 1000px) {{
            .vc-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .vc-header {{
                align-items: flex-start;
                flex-direction: column;
            }}
            .vc-title {{
                text-align: left;
            }}
        }}

        @media (max-width: 650px) {{
            .vc-grid {{
                grid-template-columns: 1fr;
            }}
            .vc-hero h2 {{
                font-size: 27px;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True
)


st.sidebar.markdown(
    f"""
    <div style="padding: 10px 0 18px 0;">
        <div style="width:190px; margin-bottom:10px;">
            {logo_html()}
        </div>
        <div style="font-size:13px;color:{VC_MUTED};">
            Portal Regional CN
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


st.markdown(
    f"""
    <div class="vc-header">
        <div class="vc-logo">
            {logo_html()}
        </div>
        <div class="vc-title">
            <h1>Sistema CN</h1>
            <p>Performance Industrial | Votorantim Cimentos</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="vc-hero">
        <h2>Portal de Indicadores Operacionais</h2>
        <p>
            Acompanhe consolidado mensal, farol de metas, ST Heatmap e FD Multiflex em um unico ambiente.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='vc-section-title'>Acesso rapido</div>", unsafe_allow_html=True)

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
    <div class="vc-grid">
        <div class="vc-card">
            <h3>Consolidacao</h3>
            <p>Upload e processamento dos arquivos mensais.</p>
        </div>
        <div class="vc-card">
            <h3>Dashboard Consolidado</h3>
            <p>Farol MTD, status por planta e historico.</p>
        </div>
        <div class="vc-card">
            <h3>ST & FD</h3>
            <p>Heatmaps diarios com exportacao em PNG e HTML.</p>
        </div>
        <div class="vc-card">
            <h3>Metas</h3>
            <p>Cadastro e atualizacao das metas do ano.</p>
        </div>
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
