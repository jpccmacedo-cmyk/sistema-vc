import streamlit as st

st.set_page_config(
    page_title="Sistema Excel CN",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.hero {
    padding: 30px;
    border-radius: 22px;
    background: linear-gradient(135deg, #eff6ff 0%, #ffffff 55%, #ecfeff 100%);
    border: 1px solid #dbeafe;
    margin-bottom: 26px;
}
.title-main {
    font-size: 2.4rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 6px;
}
.subtitle {
    color: #64748b;
    font-size: 1.05rem;
}
.card {
    padding: 22px;
    border-radius: 18px;
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
    min-height: 210px;
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
.step {
    padding: 15px 18px;
    border-radius: 14px;
    border: 1px solid #e2e8f0;
    background: white;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("📊 Sistema Excel CN")
st.sidebar.caption("Consolidação + dashboard histórico")
st.sidebar.info("Use o menu lateral para acessar as páginas.")

st.markdown("""
<div class="hero">
    <div class="pill">Portal gerencial</div>
    <div class="title-main">Sistema de Consolidação e Dashboard</div>
    <div class="subtitle">
        Gere arquivos consolidados, salve o histórico automaticamente e acompanhe os indicadores por planta.
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card">
        <div class="pill">Etapa 1</div>
        <h3>📁 Consolidação</h3>
        <p>Use esta página para gerar os consolidados. Quando o arquivo for criado, ele deve ser salvo no histórico.</p>
        <p><b>Saída esperada:</b> Excel consolidado com abas COB, CUI, EDE, NOB, PVE, SOB e XAM.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Consolidacao.py", label="Abrir Consolidação", icon="📁")

with col2:
    st.markdown("""
    <div class="card">
        <div class="pill">Etapa 2</div>
        <h3>📊 Dashboard</h3>
        <p>O dashboard lê automaticamente os consolidados salvos e extrai indicadores das células mapeadas.</p>
        <p><b>Inclui:</b> filtros, tabela, comparativo por planta e histórico.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Dashboard_Consolidado.py", label="Abrir Dashboard", icon="📊")

with col3:
    st.markdown("""
    <div class="card">
        <div class="pill">Histórico</div>
        <h3>🕘 Histórico automático</h3>
        <p>Todos os consolidados registrados ficam em <code>data/consolidados</code> e são listados no dashboard.</p>
        <p><b>Observação:</b> em nuvem, use armazenamento persistente externo no futuro.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.subheader("🚀 Fluxo de uso")
st.markdown("""
<div class="step"><b>1.</b> Acesse a página <b>Consolidação</b>.</div>
<div class="step"><b>2.</b> Gere ou registre um arquivo consolidado.</div>
<div class="step"><b>3.</b> Acesse a página <b>Dashboard Consolidado</b>.</div>
<div class="step"><b>4.</b> Escolha o consolidado e acompanhe os indicadores.</div>
""", unsafe_allow_html=True)
