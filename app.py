import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Sistema Excel CN",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# ESTILO VISUAL DA HOME
# =========================
st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .hero {
        padding: 28px;
        border-radius: 22px;
        background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 50%, #ecfeff 100%);
        border: 1px solid #dbeafe;
        margin-bottom: 24px;
    }
    .card {
        padding: 22px;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
        min-height: 205px;
    }
    .card h3 {
        margin-top: 0;
        color: #0f172a;
    }
    .card p {
        color: #64748b;
        font-size: 0.96rem;
    }
    .pill {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: #dbeafe;
        color: #1d4ed8;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .step-box {
        padding: 16px 18px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        background: #ffffff;
        margin-bottom: 10px;
    }
    .small-muted {
        color: #64748b;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("📊 Sistema Excel CN")
st.sidebar.caption("Consolidação e dashboards gerenciais")
st.sidebar.info("Use o menu acima para acessar as páginas do sistema.")

st.markdown("""
<div class="hero">
    <div class="pill">Portal interno</div>
    <div class="main-title">Sistema de Consolidação e Dashboards</div>
    <div class="subtitle">
        Centralize a consolidação dos arquivos Excel e acompanhe os indicadores ST & FD em um único lugar.
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card">
        <div class="pill">1ª etapa</div>
        <h3>📁 Consolidação Gerencial</h3>
        <p>Envie os arquivos Excel, selecione as datas disponíveis e gere os consolidados gerenciais por planta.</p>
        <p><b>Ideal para:</b> fechamento diário, conferência e padronização.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Consolidacao.py", label="Abrir consolidação", icon="📁")

with col2:
    st.markdown("""
    <div class="card">
        <div class="pill">2ª etapa</div>
        <h3>📈 Dashboard ST & FD</h3>
        <p>Visualize heatmaps, filtros por planta e acompanhamento histórico dos indicadores ST e FD Multiflex.</p>
        <p><b>Ideal para:</b> análise rápida dos KPIs e acompanhamento mensal.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Dashboard_ST_FD.py", label="Abrir dashboard", icon="📈")

with col3:
    st.markdown("""
    <div class="card">
        <div class="pill">Suporte</div>
        <h3>ℹ️ Como usar</h3>
        <p>Comece pela consolidação. Depois use o dashboard para analisar os indicadores do Excel consolidado ou dos arquivos de acompanhamento.</p>
        <p><b>Dica:</b> mantenha os nomes das abas conforme o padrão esperado.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.subheader("🚀 Fluxo recomendado")

st.markdown("""
<div class="step-box"><b>1.</b> Acesse <b>Consolidação Gerencial</b> no menu lateral.</div>
<div class="step-box"><b>2.</b> Envie os arquivos Excel necessários para consolidar.</div>
<div class="step-box"><b>3.</b> Gere e baixe o consolidado.</div>
<div class="step-box"><b>4.</b> Acesse <b>Dashboard ST & FD</b> para visualizar os indicadores.</div>
""", unsafe_allow_html=True)

st.info("Para ativar a consolidação: mova o código do seu antigo app.py para o arquivo pages/1_Consolidacao.py.")
