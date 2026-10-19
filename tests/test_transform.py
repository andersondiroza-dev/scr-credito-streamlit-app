"""Testes das regras de limpeza (transform). Cada regra documentada no README tem um teste."""
import pandas as pd
import pytest

from src import transform


def linha_bruta(**alteracoes) -> dict:
    """Uma linha no formato exato do CSV do BCB (tudo texto, números no padrão brasileiro)."""
    base = {
        "data_base": "2025-12-31", "uf": "SC", "segmento": "Banco", "cliente": "PF",
        "cnae_ocupacao": "Assalariado", "porte": "Até 1 salário mínimo",
        "modalidade": "Empréstimos", "submodalidade": "Crédito pessoal",
        "origem": "Sem destinação específica", "indexador": "Prefixado",
        "numero_de_operacoes": "10",
        "carteira_a_vencer": "900,00", "vencido_de_15_ate_90_dias": "40,00",
        "carteira_vencida": "100,00", "carteira_ativa": "1.000,00",
        "carteira_inadimplencia": "60,00", "ativo_problematico": "80,00",
    }
    base.update(alteracoes)
    return base


def test_converter_valor_br():
    serie = pd.Series(["1.234,56", "0,00", "-12,50", " 7,10 "])
    assert transform.converter_valor_br(serie).tolist() == [1234.56, 0.0, -12.5, 7.1]


def test_converter_valor_br_rejeita_texto_invalido():
    with pytest.raises(ValueError):
        transform.converter_valor_br(pd.Series(["abc"]))


def test_supressao_vira_zero_e_e_contada():
    resultado = transform.tratar_supressao(pd.Series(["5", "-1", "0"]))
    assert resultado["numero_operacoes"].tolist() == [5, 0, 0]
    assert resultado["operacao_suprimida"].tolist() == [0, 1, 0]


def test_supressao_rejeita_negativo_diferente_de_menos_um():
    with pytest.raises(ValueError):
        transform.tratar_supressao(pd.Series(["-2"]))


def test_limpar_mes_converte_tipos_e_cria_colunas():
    df = pd.DataFrame([linha_bruta(modalidade="Financiamentos  rurais ", origem="Com destinação específica")])
    limpo = transform.limpar_mes(df)
    linha = limpo.iloc[0]
    assert linha["ano_mes"] == "2025-12"
    assert linha["modalidade"] == "Financiamentos rurais"  # espaços normalizados
    assert linha["grupo_credito"] == "Direcionado"
    assert linha["regiao"] == "Sul"
    assert linha["carteira_ativa"] == 1000.0
    assert "indexador" not in limpo.columns  # coluna descartada por minimização


def test_limpar_mes_remove_duplicadas_exatas():
    df = pd.DataFrame([linha_bruta(), linha_bruta()])
    assert len(transform.limpar_mes(df)) == 1


def test_limpar_mes_preenche_categoria_ausente():
    df = pd.DataFrame([linha_bruta(porte=None)])
    assert transform.limpar_mes(df).iloc[0]["porte"] == "Não informado"


def test_limpar_mes_falha_com_origem_desconhecida():
    df = pd.DataFrame([linha_bruta(origem="Outra coisa")])
    with pytest.raises(ValueError, match="origem"):
        transform.limpar_mes(df)


def test_limpar_mes_falha_sem_coluna_obrigatoria():
    df = pd.DataFrame([linha_bruta()]).drop(columns=["carteira_ativa"])
    with pytest.raises(ValueError, match="carteira_ativa"):
        transform.limpar_mes(df)


def test_relatorio_qualidade():
    df = pd.DataFrame([linha_bruta(), linha_bruta(), linha_bruta(numero_de_operacoes="-1", porte=None)])
    rel = transform.relatorio_qualidade(df)
    assert rel == {"ano_mes": "2025-12", "linhas": 3, "nulos": 1, "duplicadas": 1, "combinacoes_suprimidas": 1}
