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


import zipfile as _zipfile


def _csv_bcb(linhas: list[dict]) -> str:
    """Gera um CSV idêntico ao do BCB: separador ';', todos os campos entre aspas, BOM."""
    colunas = list(linhas[0].keys())
    corpo = [";".join(f'"{l[c]}"' for c in colunas) for l in linhas]
    return "﻿" + ";".join(colunas) + "\n" + "\n".join(corpo) + "\n"


def test_agregar_soma_metricas_e_renomeia_supressao():
    df = transform.limpar_mes(pd.DataFrame([
        linha_bruta(cnae_ocupacao="Assalariado"),
        linha_bruta(cnae_ocupacao="Autônomo", numero_de_operacoes="-1"),
    ]))
    agregado = transform.agregar(df, ["ano_mes", "cliente"])
    assert len(agregado) == 1
    assert agregado.iloc[0]["carteira_ativa"] == 2000.0
    assert agregado.iloc[0]["numero_operacoes"] == 10
    assert agregado.iloc[0]["combinacoes_suprimidas"] == 1


def test_validar_total_aceita_dentro_da_tolerancia():
    resumo = pd.DataFrame({"ano_mes": ["2025-12", "2025-12"], "carteira_ativa": [500.0, 505.0]})
    assert transform.validar_total(resumo, "2025-12", esperado=1000.0, tolerancia=0.01) == 1005.0


def test_validar_total_rejeita_divergencia():
    resumo = pd.DataFrame({"ano_mes": ["2025-12"], "carteira_ativa": [900.0]})
    with pytest.raises(ValueError, match="diverge"):
        transform.validar_total(resumo, "2025-12", esperado=1000.0, tolerancia=0.01)


def test_executar_ponta_a_ponta_com_zip_sintetico(tmp_path):
    raw, processed = tmp_path / "raw", tmp_path / "processed"
    raw.mkdir()
    with _zipfile.ZipFile(raw / "scrdata_2099.zip", "w") as z:
        z.writestr("scrdata_209901.csv", _csv_bcb([linha_bruta(data_base="2099-01-31", cnae_ocupacao="Comércio; reparação")]))
        z.writestr("scrdata_209902.csv", _csv_bcb([linha_bruta(data_base="2099-02-28")]))

    tabelas = transform.executar(dir_raw=raw, dir_processed=processed, anos=(2099,), meses_por_ano=2, validar=False)

    assert tabelas["resumo_mensal"]["ano_mes"].tolist() == ["2099-01", "2099-02"]
    assert set(tabelas["fato_setor"]["cnae_ocupacao"]) == {"Comércio; reparação", "Assalariado"}
    assert len(tabelas["qualidade_mensal"]) == 2
    for nome in ["fato_credito", "fato_setor", "resumo_mensal", "qualidade_mensal"]:
        assert (processed / f"{nome}.parquet").exists()
    lido = pd.read_parquet(processed / "fato_credito.parquet")
    assert lido["segmento"].dtype == "category"
    assert lido["ano_mes"].dtype != "category"  # continua texto para os filtros >= e <=


def test_executar_falha_se_faltar_mes(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    with _zipfile.ZipFile(raw / "scrdata_2099.zip", "w") as z:
        z.writestr("scrdata_209901.csv", _csv_bcb([linha_bruta(data_base="2099-01-31")]))
    with pytest.raises(ValueError, match="esperados 12"):
        transform.executar(dir_raw=raw, dir_processed=tmp_path / "p", anos=(2099,), validar=False)


def test_executar_falha_se_zip_ausente(tmp_path):
    with pytest.raises(FileNotFoundError, match="src.extract"):
        transform.executar(dir_raw=tmp_path, dir_processed=tmp_path / "p", anos=(2099,), validar=False)
