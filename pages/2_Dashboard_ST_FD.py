import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(
    page_title="Dashboard ST & FD",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Dashboard ST & FD")
st.caption("Acompanhe os indicadores ST e FD Multiflex com filtros e histórico.")

with st.expander("Como usar o dashboard", expanded=False):
    st.markdown("""
    1. Clique na área de upload dentro do dashboard.
    2. Envie o Excel com as abas esperadas.
    3. Use os filtros de ano, mês e plantas.
    4. Se o histórico local estiver ativado no HTML, os dados permanecem ao sair e voltar no mesmo navegador.
    """)

html_path = Path(__file__).resolve().parent.parent / "dashboard_st_fd.html"

if not html_path.exists():
    st.error("Arquivo dashboard_st_fd.html não encontrado. Coloque ele na mesma pasta do app.py.")
else:
    html_dashboard = html_path.read_text(encoding="utf-8")
    components.html(html_dashboard, height=1250, scrolling=True)
