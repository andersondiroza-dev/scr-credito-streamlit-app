from src import analysis, graficos, utils


def _tem_padrao(fig, titulo):
    assert fig.layout.title.text == titulo
    assert fig.layout.xaxis.title.text and fig.layout.yaxis.title.text
    assert any(utils.FONTE in a.text for a in fig.layout.annotations)


def test_linhas_mensais(fato_exemplo):
    serie = analysis.serie_mensal(fato_exemplo, por="cliente")
    fig = graficos.linhas_mensais(serie, "taxa_inadimplencia", "Inadimplência", "% da carteira", por="cliente")
    _tem_padrao(fig, "Inadimplência")
    assert len(fig.data) == 2


def test_linhas_mensais_marca_jan_2025(fato_exemplo):
    serie = analysis.serie_mensal(fato_exemplo.assign(ano_mes=fato_exemplo["ano_mes"].replace("2025-12", "2025-01")))
    fig = graficos.linhas_mensais(serie, "taxa_inadimplencia", "Inadimplência", "% da carteira", marcar_jan_2025=True)
    assert any("Res. CMN 4.966" in a.text for a in fig.layout.annotations)


def test_quadrante(fato_exemplo):
    cxr = analysis.crescimento_x_risco(fato_exemplo, "2024-12", "2025-12", chaves=("segmento", "cliente"), carteira_minima=0)
    _tem_padrao(graficos.quadrante(cxr), "Quadrante de risco: crescimento × inadimplência")


def test_barras_e_boxplot(fato_exemplo):
    part, _ = analysis.participacao_e_hhi(fato_exemplo, "2025-12")
    _tem_padrao(graficos.barras(part, "segmento", "participacao_pct", "Participação", "% da carteira"), "Participação")
    mensal = analysis.serie_mensal(fato_exemplo, por="uf")
    _tem_padrao(graficos.boxplot(mensal, "uf", "Distribuição por UF"), "Distribuição por UF")
