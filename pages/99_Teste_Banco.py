import streamlit as st
from sqlalchemy import text

from database.connection import get_engine

st.set_page_config(
    page_title="Teste Banco",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Teste de Conexão com Banco")

try:
    engine = get_engine()

    with engine.begin() as conn:
        resultado = conn.execute(text("SELECT 1 AS teste")).fetchone()

    st.success("Conexão com o banco realizada com sucesso!")
    st.write("Resultado do teste:", resultado)

except Exception as e:
    st.error("Erro ao conectar no banco.")
    st.exception(e)
