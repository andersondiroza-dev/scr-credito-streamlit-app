"""Testes dos indicadores. Os valores esperados foram calculados à mão (ver conftest.py)."""
import math

import pandas as pd
import pytest

from src import analysis


def test_taxa_percentual_escalar_e_divisao_por_zero():
    assert analysis.taxa_percentual(5, 100) == 5.0
    assert math.isnan(analysis.taxa_percentual(5, 0))


def test_taxa_percentual_series():
    resultado = analysis.taxa_percentual(pd.Series([1.0, 2.0]), pd.Series([10.0, 0.0]))
    assert resultado.iloc[0] == 10.0
    assert math.isnan(resultado.iloc[1])


def test_filtrar_por_periodo_e_listas(fato_exemplo):
    f = analysis.filtrar(fato_exemplo, "2025-12", "2025-12", clientes=["PF"], segmentos=["Fintech"])
    assert len(f) == 1 and f.iloc[0]["carteira_ativa"] == 200.0


def test_filtrar_lista_vazia_nao_filtra(fato_exemplo):
    assert len(analysis.filtrar(fato_exemplo, "2024-12", "2025-12", clientes=[])) == 6


def test_mes_base_comparacao_usa_12_meses_antes_quando_disponivel():
    meses = ["2024-01", "2024-12", "2025-12"]
    assert analysis.mes_base_comparacao(meses, "2024-01", "2025-12") == "2024-12"


def test_mes_base_comparacao_cai_para_inicio_do_periodo():
    meses = ["2025-01", "2025-06"]
    assert analysis.mes_base_comparacao(meses, "2025-01", "2025-06") == "2025-01"


def test_serie_mensal_total(fato_exemplo):
    serie = analysis.serie_mensal(fato_exemplo)
    dez25 = serie.set_index("ano_mes").loc["2025-12"]
    assert dez25["carteira_ativa"] == 2200.0
    assert dez25["taxa_inadimplencia"] == pytest.approx(114 / 2200 * 100)


def test_serie_mensal_por_grupo(fato_exemplo):
    serie = analysis.serie_mensal(fato_exemplo, por="cliente")
    assert set(serie.columns) >= {"ano_mes", "cliente", "taxa_inadimplencia"}
    assert len(serie) == 4


def test_kpis(fato_exemplo):
    k = analysis.kpis(fato_exemplo, "2024-12", "2025-12")
    assert k["carteira_base"] == 2000.0
    assert k["carteira_ref"] == 2200.0
    assert k["crescimento_pct"] == pytest.approx(10.0)
    assert k["inadimplencia_ref_pct"] == pytest.approx(114 / 2200 * 100)
    assert k["participacao_fintech_pct"] == pytest.approx(200 / 2200 * 100)


def test_kpis_sem_dados_nao_quebra(fato_exemplo):
    k = analysis.kpis(fato_exemplo.iloc[0:0], "2024-12", "2025-12")
    assert k["carteira_ref"] == 0.0
    assert math.isnan(k["crescimento_pct"])


def test_crescimento_x_risco(fato_exemplo):
    cxr = analysis.crescimento_x_risco(fato_exemplo, "2024-12", "2025-12", chaves=("segmento", "cliente"), carteira_minima=0)
    fintech = cxr.set_index(["segmento", "cliente"]).loc[("Fintech", "PF")]
    assert fintech["crescimento_pct"] == pytest.approx(100.0)
    assert fintech["inadimplencia_base_pct"] == pytest.approx(10.0)
    assert fintech["inadimplencia_ref_pct"] == pytest.approx(15.0)
    assert fintech["variacao_inadimplencia_pp"] == pytest.approx(5.0)


def test_crescimento_x_risco_exclui_carteira_pequena(fato_exemplo):
    cxr = analysis.crescimento_x_risco(fato_exemplo, "2024-12", "2025-12", chaves=("segmento", "cliente"), carteira_minima=500)
    assert ("Fintech" in cxr["segmento"].tolist()) is False


def test_correlacao_spearman_perfeita():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})
    r = analysis.correlacao_spearman(df, "x", "y")
    assert r["rho"] == pytest.approx(1.0)
    assert r["n"] == 5


def test_correlacao_spearman_poucos_pontos():
    r = analysis.correlacao_spearman(pd.DataFrame({"x": [1, 2], "y": [2, 1]}), "x", "y")
    assert math.isnan(r["rho"]) and r["n"] == 2


def test_interpretar_spearman():
    assert "positiva" in analysis.interpretar_spearman(0.6, 0.001)
    assert "não é estatisticamente significativa" in analysis.interpretar_spearman(0.1, 0.4)


def test_tendencia_linear_reta_perfeita():
    t = analysis.tendencia_linear([1.0, 1.5, 2.0, 2.5])
    assert t["inclinacao"] == pytest.approx(0.5)
    assert t["r2"] == pytest.approx(1.0)
    assert t["ic95_inferior"] == pytest.approx(0.5)
    assert t["ic95_superior"] == pytest.approx(0.5)


def test_participacao_e_hhi(fato_exemplo):
    part, hhi = analysis.participacao_e_hhi(fato_exemplo, "2025-12")
    banco = part.set_index("segmento").loc["Banco", "participacao_pct"]
    assert banco == pytest.approx(2000 / 2200 * 100)
    assert hhi == pytest.approx((2000 / 2200 * 100) ** 2 + (200 / 2200 * 100) ** 2)


def test_classificar_hhi():
    assert analysis.classificar_hhi(1000).startswith("baixa")
    assert analysis.classificar_hhi(2000).startswith("moderada")
    assert analysis.classificar_hhi(8000).startswith("alta")


def test_descritivas_por_grupo(fato_exemplo):
    d = analysis.descritivas_por_grupo(fato_exemplo, "cliente")
    assert d.loc["PJ", "mediana"] == pytest.approx(2.0)
    assert d.loc["PJ", "n_meses"] == 2
    assert list(d.columns) == ["media", "mediana", "desvio_padrao", "q1", "q3", "minimo", "maximo", "n_meses"]
