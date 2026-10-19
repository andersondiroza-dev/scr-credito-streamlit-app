"""Testes de fumaça: o app abre sem erro com dados sintéticos e mostra aviso quando faltam dados."""
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src import config

# Nesta versão do Streamlit, AppTest resolve caminhos a partir da pasta do teste; usamos o caminho completo.
APP = str(config.RAIZ_PROJETO / "app.py")


@pytest.fixture
def app_teste(tmp_path, monkeypatch, fato_exemplo):
    """Grava Parquets sintéticos em uma pasta temporária e aponta o app para ela."""
    fato_exemplo.to_parquet(tmp_path / "fato_credito.parquet")
    pd.DataFrame({"ano_mes": ["2024-12", "2025-12"], "cliente": ["PF", "PF"], "carteira_ativa": [1.0, 2.0]}).to_parquet(tmp_path / "resumo_mensal.parquet")
    pd.DataFrame({"ano_mes": ["2025-12"], "cliente": ["PF"], "cnae_ocupacao": ["Assalariado"], "carteira_ativa": [1.0], "carteira_inadimplencia": [0.1]}).to_parquet(tmp_path / "fato_setor.parquet")
    pd.DataFrame({"ano_mes": ["2025-12"], "linhas": [10], "nulos": [0], "duplicadas": [0], "combinacoes_suprimidas": [1]}).to_parquet(tmp_path / "qualidade_mensal.parquet")
    monkeypatch.setattr(config, "DIR_PROCESSED", tmp_path)
    st.cache_data.clear()
    return AppTest.from_file(APP, default_timeout=30)


def test_inicio_abre_sem_erro(app_teste):
    at = app_teste.run()
    assert not at.exception
    assert len(at.metric) == 4


def test_mensagem_quando_parquet_falta(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DIR_PROCESSED", tmp_path)
    st.cache_data.clear()
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert any("python -m src.transform" in e.value for e in at.error)


PAGINAS = ["pages/2_evolucao.py", "pages/3_crescimento_risco.py", "pages/4_quem_empresta.py",
           "pages/5_onde_e_o_que.py", "pages/6_metodologia.py"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_paginas_abrem_sem_erro(app_teste, pagina):
    at = app_teste.run()
    at.switch_page(pagina).run()
    assert not at.exception, at.exception
