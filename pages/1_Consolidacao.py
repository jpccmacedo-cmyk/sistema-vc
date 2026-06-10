import streamlit as st
from utils.historico import registrar_arquivo_consolidado_bytes, salvar_resultados_no_historico

st.set_page_config(
    page_title="Consolidação",
    page_icon="📁",
    layout="wide"
)

st.title("📁 Consolidação Gerencial")
st.caption("Página para gerar consolidados e registrar automaticamente no histórico do dashboard.")

st.info(
    "Nesta versão do zero, deixei uma área para registrar manualmente um consolidado já gerado. "
    "Depois, você cola seu código real de consolidação nesta página e chama salvar_resultados_no_historico(resultados)."
)

st.subheader("1. Registrar consolidado já gerado")
st.write("Use este bloco para testar o dashboard agora: envie um arquivo consolidado Excel já pronto.")

arquivo_consolidado = st.file_uploader(
    "Enviar arquivo consolidado para o histórico",
    type=["xlsx", "xlsm"]
)

if st.button("💾 Salvar consolidado no histórico", disabled=arquivo_consolidado is None):
    registro = registrar_arquivo_consolidado_bytes(
        nome_arquivo=arquivo_consolidado.name,
        conteudo_bytes=arquivo_consolidado.getvalue(),
        origem="upload_manual"
    )

    st.success(f"Consolidado salvo no histórico: {registro['nome_arquivo']}")

    st.page_link(
        "pages/2_Dashboard_Consolidado.py",
        label="Abrir dashboard",
        icon="📊"
    )

st.divider()

st.subheader("2. Onde encaixar seu código real de consolidação")

st.markdown("""
Quando você colar seu código antigo aqui, procure a parte onde ele gera a variável `resultados`, algo assim:

```python
resultados = processar_multiplas_datas(
    datas_selecionadas,
    arquivos_salvos,
    data_referencia,
    copiar_estilos=copiar_estilos
)
salvar_resultados_no_historico(resultados)

st.success("Consolidado(s) salvo(s) no histórico do dashboard.")
