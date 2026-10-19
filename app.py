"""Ponto de entrada do app Streamlit: Panorama do Crédito Nacional (SCR.data).

Executar:  streamlit run app.py
Os filtros da barra lateral são criados aqui, uma vez, e valem para todas as páginas.
"""
import streamlit as st

from src import interface

st.set_page_config(page_title="Panorama do Crédito Nacional", page_icon="📊", layout="wide")

dados = interface.carregar_dados()
st.session_state["dados"] = dados
st.session_state["filtros"] = interface.barra_lateral(dados["fato_credito"])

paginas = st.navigation([
    st.Page("pages/1_inicio.py", title="Início", icon="🏠", default=True),
    st.Page("pages/2_evolucao.py", title="Evolução", icon="📈"),
    st.Page("pages/3_crescimento_risco.py", title="Crescimento x Risco", icon="🎯"),
    st.Page("pages/4_quem_empresta.py", title="Quem empresta", icon="🏦"),
    st.Page("pages/5_onde_e_o_que.py", title="Onde e o quê", icon="🗺️"),
    st.Page("pages/6_metodologia.py", title="Metodologia e limites", icon="📚"),
])
paginas.run()
