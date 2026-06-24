import streamlit as st

from utils.ui_vc import (
    configurar_pagina,
    aplicar_css_global,
    render_header,
    render_footer,
)


configurar_pagina(
    titulo="Sistema CN | Votorantim Cimentos",
    icone=":bar_chart:",
    layout="wide"
)

aplicar_css_global(
    max_width="900px",
    esconder_sidebar=True
)


def page_exists(path):
    from pathlib import Path
    return Path(path).exists()


def menu_link(path, label):
    if page_exists(path):
        st.page_link(path, label=label)
    else:
        st.caption("Página não encontrada: " + path)


render_header(
    titulo="Sistema CN",
    subtitulo="Performance Industrial | Regional Centro-Norte"
)


st.markdown(
    """
    <div class="vc-card">
        <h2 style="margin-top:0; color:#172033;">Portal de Indicadores Operacionais</h2>
        <p style="color:#667085; margin-bottom:20px;">
            Selecione uma página para acessar.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

menu_link("pages/1_Consolidacao.py", "Consolidação")
menu_link("pages/2_Dashboard_Consolidado.py", "Dashboard Consolidado")
menu_link("pages/3_Dashboard_ST_FD.py", "Dashboard ST & FD")
menu_link("pages/4_Metas.py", "Metas")

render_footer()
