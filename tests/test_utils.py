from src import utils


def test_formatar_reais_escalas():
    assert utils.formatar_reais(7.444e12) == "R$ 7,44 tri"
    assert utils.formatar_reais(7.4e9) == "R$ 7,40 bi"
    assert utils.formatar_reais(1.5e6) == "R$ 1,50 mi"
    assert utils.formatar_reais(1234.5) == "R$ 1.234,50"
    assert utils.formatar_reais(float("nan")) == "n/d"


def test_formatar_pct_e_pp():
    assert utils.formatar_pct(5.1478) == "5,15%"
    assert utils.formatar_pp(0.123) == "+0,12 p.p."
    assert utils.formatar_pp(-1.5) == "-1,50 p.p."
    assert utils.formatar_pct(float("nan")) == "n/d"


def test_nome_mes():
    assert utils.nome_mes("2025-12") == "dez/2025"
    assert utils.nome_mes("2024-01") == "jan/2024"
