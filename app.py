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
# Configuracoes visuais
# ============================================================

LOGO_URL = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Logotipo_da_Votorantim_Cimentos.svg"
LOCAL_LOGO_PATHS = [
    "assets/votorantim_cimentos_logo.svg",
    "assets/votorantim_cimentos_logo.png",
    "assets/logo_votorantim.png",
    "assets/logo.png",
]

VC_BLUE = "#184478"
VC_LIGHT_BLUE = "#7BBFE3"
VC_GRAY = "#707270"
VC_NAVY = "#0F218B"
VC_BG = "#F4F7FB"
VC_CARD = "#FFFFFF"
VC_TEXT = "#0F172A"
VC_MUTED = "#64748B"
VC_BORDER = "#D8E2EE"
VC_SUCCESS = "#00A85A"
VC_WARNING = "#F59E0B"
VC_DANGER = "#DC2626"


st.markdown(
    f"""
    <style>
        :root {{
            --vc-blue: {VC_BLUE};
            --vc-light-blue: {VC_LIGHT_BLUE};
            --vc-gray: {VC_GRAY};
            --vc-bg: {VC_BG};
            --vc-card: {VC_CARD};
            --vc-text: {VC_TEXT};
            --vc-muted: {VC_MUTED};
            --vc-border: {VC_BORDER};
        }}

        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(123, 191, 227, 0.28), transparent 34%),
                linear-gradient(180deg, #F8FBFF 0%, #F4F7FB 48%, #EEF4FA 100%);
            color: var(--vc-text);
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F2F7FC 100%);
            border-right: 1px solid var(--vc-border);
        }}

        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{
            color: #213047;
        }}

        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }}

        .vc-topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 14px 18px;
            margin-bottom: 18px;
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(216, 226, 238, 0.95);
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(15, 33, 139, 0.08);
            backdrop-filter: blur(10px);
        }}

        .vc-brand {{
            display: flex;
            align-items: center;
            gap: 14px;
            min-width: 260px;
        }}

        .vc-logo-box {{
            width: 184px;
            min-width: 184px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            overflow: hidden;
        }}

        .vc-logo-box img {{
            max-width: 178px;
            max-height: 44px;
            object-fit: contain;
        }}

        .vc-system-name {{
            border-left: 1px solid #D7E1EC;
            padding-left: 14px;
        }}

        .vc-system-name .title {{
            font-size: 15px;
            line-height: 1.2;
            font-weight: 800;
            color: var(--vc-blue);
            letter-spacing: 0.1px;
        }}

        .vc-system-name .subtitle {{
            font-size: 12px;
            color: var(--vc-muted);
            margin-top: 2px;
        }}

        .vc-pill-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: flex-end;
        }}

        .vc-pill {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 8px 11px;
            background: #F2F8FD;
            border: 1px solid #D9EAF8;
            border-radius: 999px;
            font-size: 12px;
            color: #274263;
            white-space: nowrap;
        }}

        .vc-dot {{
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--vc-light-blue);
            display: inline-block;
        }}

        .vc-hero {{
            position: relative;
            padding: 34px 34px 30px 34px;
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(24,68,120,0.96), rgba(15,33,139,0.92)),
                radial-gradient(circle at top right, rgba(123,191,227,0.45), transparent 36%);
            color: #FFFFFF;
            box-shadow: 0 24px 60px rgba(24,68,120,0.22);
            overflow: hidden;
            margin-bottom: 24px;
        }}

        .vc-hero:after {{
            content: "";
            position: absolute;
            right: -90px;
            top: -90px;
            width: 260px;
            height: 260px;
            background: rgba(123,191,227,0.25);
            border-radius: 999px;
        }}

        .vc-hero:before {{
            content: "";
            position: absolute;
            right: 80px;
            bottom: -95px;
            width: 220px;
            height: 220px;
            background: rgba(255,255,255,0.08);
            border-radius: 999px;
        }}

        .vc-hero-content {{
            position: relative;
            z-index: 2;
            max-width: 860px;
        }}

        .vc-eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.13);
            border: 1px solid rgba(255,255,255,0.20);
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.2px;
            margin-bottom: 16px;
        }}

        .vc-hero h1 {{
            font-size: 42px;
            line-height: 1.05;
            margin: 0 0 12px 0;
            color: #FFFFFF;
            font-weight: 900;
            letter-spacing: -0.8px;
        }}

        .vc-hero p {{
            font-size: 16px;
            line-height: 1.6;
            color: rgba(255,255,255,0.88);
            max-width: 780px;
            margin: 0;
        }}

        .vc-section-title {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            margin: 28px 0 12px 0;
        }}

        .vc-section-title h2 {{
            font-size: 23px;
            margin: 0;
            color: #13233A;
            font-weight: 900;
        }}

        .vc-section-title span {{
            color: var(--vc-muted);
            font-size: 13px;
        }}

        .vc-card-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 16px;
            margin-bottom: 22px;
        }}

        .vc-card {{
            background: rgba(255,255,255,0.94);
            border: 1px solid var(--vc-border);
            border-radius: 22px;
            padding: 18px 18px 16px 18px;
            box-shadow: 0 12px 30px rgba(15, 33, 139, 0.06);
            min-height: 154px;
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }}

        .vc-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 18px 42px rgba(15, 33, 139, 0.12);
            border-color: rgba(123,191,227,0.9);
        }}

        .vc-icon {{
            width: 42px;
            height: 42px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(123,191,227,0.28), rgba(24,68,120,0.10));
            color: var(--vc-blue);
            font-size: 22px;
            margin-bottom: 14px;
        }}

        .vc-card h3 {{
            font-size: 16px;
            margin: 0 0 8px 0;
            font-weight: 900;
            color: #10243E;
        }}

        .vc-card p {{
            font-size: 13px;
            color: var(--vc-muted);
            line-height: 1.45;
            margin: 0 0 12px 0;
        }}

        .vc-card .status {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            font-size: 12px;
            color: #244061;
            background: #F4F9FD;
            border: 1px solid #DFEDF7;
            border-radius: 999px;
            padding: 6px 10px;
        }}

        .vc-metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: 14px 0 26px 0;
        }}

        .vc-mini-metric {{
            background: rgba(255,255,255,0.82);
            border: 1px solid var(--vc-border);
            border-radius: 18px;
            padding: 15px 16px;
        }}

        .vc-mini-metric .label {{
            font-size: 12px;
            color: var(--vc-muted);
            margin-bottom: 6px;
        }}

        .vc-mini-metric .value {{
            font-size: 24px;
            color: var(--vc-blue);
            font-weight: 900;
            line-height: 1;
        }}

        .vc-mini-metric .hint {{
            font-size: 12px;
            color: #7890A8;
            margin-top: 6px;
        }}

        .vc-action-panel {{
            display: grid;
            grid-template-columns: 1.25fr 0.75fr;
            gap: 16px;
            margin-top: 10px;
        }}

        .vc-panel {{
            background: rgba(255,255,255,0.90);
            border: 1px solid var(--vc-border);
            border-radius: 22px;
            padding: 20px;
            box-shadow: 0 12px 30px rgba(15, 33, 139, 0.06);
        }}

        .vc-panel h3 {{
            margin: 0 0 10px 0;
            font-size: 17px;
            color: #10243E;
            font-weight: 900;
        }}

        .vc-panel p, .vc-panel li {{
            color: var(--vc-muted);
            font-size: 13px;
            line-height: 1.55;
        }}

        .vc-footer {{
            margin-top: 28px;
            padding: 14px 2px;
            color: #7B8DA4;
            font-size: 12px;
            text-align: center;
        }}

        div[data-testid="stPageLink"] a {{
            border-radius: 14px;
            border: 1px solid #D8E2EE;
            background: #FFFFFF;
            padding: 12px 14px;
            text-decoration: none;
            transition: all .15s ease;
        }}

        div[data-testid="stPageLink"] a:hover {{
            border-color: var(--vc-light-blue);
            box-shadow: 0 8px 20px rgba(15, 33, 139, 0.08);
            transform: translateY(-1px);
        }}

        @media (max-width: 1050px) {{
            .vc-card-grid, .vc-metric-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .vc-action-panel {{
                grid-template-columns: 1fr;
            }}
            .vc-topbar {{
                align-items: flex-start;
                flex-direction: column;
            }}
            .vc-pill-row {{
                justify-content: flex-start;
            }}
        }}

        @media (max-width: 680px) {{
            .vc-card-grid, .vc-metric-grid {{
                grid-template-columns: 1fr;
            }}
            .vc-hero h1 {{
                font-size: 30px;
            }}
            .vc-hero {{
                padding: 26px 22px;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# Funcoes
# ============================================================

def logo_html():
    for logo_path in LOCAL_LOGO_PATHS:
        if Path(logo_path).exists():
            return f"<img src='{logo_path}' alt='Votorantim Cimentos'>"
    return f"<img src='{LOGO_URL}' alt='Votorantim Cimentos'>"


def page_exists(path):
    return Path(path).exists()


def safe_page_link(path, label, icon=None):
    if page_exists(path):
        st.page_link(path, label=label, icon=icon)
    else:
        st.markdown(
            f"""
            <div style="padding:12px 14px;border:1px dashed #CBD5E1;border-radius:14px;background:#F8FAFC;color:#64748B;font-size:13px;">
                Pagina nao encontrada: <b>{path}</b>
            </div>
            """,
            unsafe_allow_html=True
        )


def saudacao():
    hora = datetime.now().hour
    if hora < 12:
        return "Bom dia"
    if hora < 18:
        return "Boa tarde"
    return "Boa noite"


# ============================================================
# Sidebar
# ============================================================

st.sidebar.markdown(
    f"""
    <div style="padding:12px 4px 16px 4px;">
        <div style="width:180px; margin-bottom:12px;">
            {logo_html()}
        </div>
        <div style="font-size:13px;color:#64748B;line-height:1.45;">
            Sistema de dashboards operacionais da Regional CN.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("### Navegacao")
safe_page_link("pages/1_Consolidacao.py", "Consolidacao", "📥")
safe_page_link("pages/2_Dashboard_Consolidado.py", "Dashboard Consolidado", "📊")
safe_page_link("pages/3_Dashboard_ST_FD.py", "Dashboard ST & FD", "🔥")
safe_page_link("pages/4_Metas.py", "Metas", "🎯")

st.sidebar.markdown("---")
st.sidebar.caption("Votorantim Cimentos | Regional CN")


# ============================================================
# Header
# ============================================================

st.markdown(
    f"""
    <div class="vc-topbar">
        <div class="vc-brand">
            <div class="vc-logo-box">
                {logo_html()}
            </div>
            <div class="vc-system-name">
                <div class="title">Sistema de Performance Industrial</div>
                <div class="subtitle">Regional CN | Farol, ST, FD e Consolidados</div>
            </div>
        </div>
        <div class="vc-pill-row">
            <div class="vc-pill"><span class="vc-dot"></span> Operacao CN</div>
            <div class="vc-pill"><span class="vc-dot"></span> Dashboards em tempo real</div>
            <div class="vc-pill"><span class="vc-dot"></span> PostgreSQL compartilhado</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# Hero
# ============================================================

st.markdown(
    f"""
    <section class="vc-hero">
        <div class="vc-hero-content">
            <div class="vc-eyebrow">{saudacao()} | Centro-Norte</div>
            <h1>Gestao operacional integrada da Regional CN</h1>
            <p>
                Acompanhe consolidacao mensal, farol de indicadores, metas, ST Heatmap e FD Multiflex em um unico portal.
                A interface foi organizada para facilitar a leitura diaria, apoiar decisoes rapidas e padronizar a rotina de acompanhamento industrial.
            </p>
        </div>
    </section>
    """,
    unsafe_allow_html=True
)


# ============================================================
# Cards principais
# ============================================================

st.markdown(
    """
    <div class="vc-section-title">
        <h2>Modulos principais</h2>
        <span>Escolha uma area para continuar</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="vc-card-grid">
        <div class="vc-card">
            <div class="vc-icon">📥</div>
            <h3>Consolidacao</h3>
            <p>Processamento dos arquivos mensais e geracao do consolidado operacional.</p>
            <span class="status">Entrada de dados</span>
        </div>
        <div class="vc-card">
            <div class="vc-icon">🚦</div>
            <h3>Farol Consolidado</h3>
            <p>Comparativo MTD versus meta por planta, grupo e indicador.</p>
            <span class="status">Gestao de metas</span>
        </div>
        <div class="vc-card">
            <div class="vc-icon">🔥</div>
            <h3>ST & FD</h3>
            <p>Heatmaps diarios de ST e FD Multiflex com visual para print e exportacao.</p>
            <span class="status">Rotina diaria</span>
        </div>
        <div class="vc-card">
            <div class="vc-icon">🎯</div>
            <h3>Metas</h3>
            <p>Cadastro e atualizacao das metas anuais e mensais utilizadas nos dashboards.</p>
            <span class="status">Administrativo</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# Acesso rapido
# ============================================================

st.markdown(
    """
    <div class="vc-section-title">
        <h2>Acesso rapido</h2>
        <span>Atalhos para as paginas do sistema</span>
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    safe_page_link("pages/1_Consolidacao.py", "Abrir Consolidacao", "📥")

with col2:
    safe_page_link("pages/2_Dashboard_Consolidado.py", "Abrir Dashboard Consolidado", "📊")

with col3:
    safe_page_link("pages/3_Dashboard_ST_FD.py", "Abrir ST & FD", "🔥")

with col4:
    safe_page_link("pages/4_Metas.py", "Abrir Metas", "🎯")


# ============================================================
# Indicadores institucionais / orientacao
# ============================================================

st.markdown(
    """
    <div class="vc-section-title">
        <h2>Visao do portal</h2>
        <span>Padronizacao, rastreabilidade e tomada de decisao</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="vc-metric-grid">
        <div class="vc-mini-metric">
            <div class="label">Unidades acompanhadas</div>
            <div class="value">7 + CN</div>
            <div class="hint">COB, CUI, EDE, NOB, PVE, SOB, XAM e Regional CN</div>
        </div>
        <div class="vc-mini-metric">
            <div class="label">Indicadores principais</div>
            <div class="value">OEE</div>
            <div class="hint">Fornos, moagens, ensacadeiras e britagens</div>
        </div>
        <div class="vc-mini-metric">
            <div class="label">Rotina diaria</div>
            <div class="value">ST / FD</div>
            <div class="hint">Heatmaps com exportacao visual</div>
        </div>
        <div class="vc-mini-metric">
            <div class="label">Controle</div>
            <div class="value">Metas</div>
            <div class="hint">Base unica no PostgreSQL</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="vc-action-panel">
        <div class="vc-panel">
            <h3>Como usar no dia a dia</h3>
            <ul>
                <li>Use <b>Consolidacao</b> para processar e salvar novos consolidados.</li>
                <li>Acompanhe o <b>Farol Consolidado</b> para comparar resultado MTD com as metas cadastradas.</li>
                <li>Use <b>ST & FD</b> para acompanhar os heatmaps diarios e exportar imagens para reunioes.</li>
                <li>Atualize <b>Metas</b> somente quando houver revisao mensal, anual ou inclusao de novos indicadores.</li>
            </ul>
        </div>
        <div class="vc-panel">
            <h3>Governanca</h3>
            <p>
                Recomendacao: manter a pagina de Metas e as acoes de exclusao protegidas por senha de administrador.
                Assim, usuarios comuns consultam dashboards sem risco de alterar bases historicas.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="vc-footer">
        Portal de Performance Industrial | Votorantim Cimentos - Regional CN
    </div>
    """,
    unsafe_allow_html=True
)
