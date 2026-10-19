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
])
paginas.run()
