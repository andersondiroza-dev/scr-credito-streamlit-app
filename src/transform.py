"""Etapa T do ETL (Transform) e carga (Load) em Parquet.

Decisões de tratamento (cada uma tem teste em tests/test_transform.py):
1. Valores monetários vêm como texto no padrão brasileiro ("1.234,56") e viram número.
2. numero_de_operacoes = -1 significa SUPRESSÃO POR SIGILO do BCB (combinações com
   poucas operações), não erro: entra como 0 na soma e é contado em coluna própria.
3. Espaços extras nas categorias são normalizados; categoria ausente vira "Não informado".
4. Linhas duplicadas exatas são removidas.
5. grupo_credito (Livre/Direcionado) vem do campo oficial "origem".
6. Minimização: faixas de vencimento, submodalidade e indexador são descartados.
7. Validação final: o total nacional precisa bater com o valor conferido no arquivo bruto.

Uso:  python -m src.transform
"""
import zipfile
from pathlib import Path
from typing import Iterator

import pandas as pd

from src import config

# Colunas do CSV bruto de que o projeto precisa. Se o BCB mudar o layout, o ETL avisa.
COLUNAS_BRUTAS_NECESSARIAS = ["data_base", *config.COLUNAS_CATEGORICAS, "numero_de_operacoes", *config.COLUNAS_MONETARIAS]


def converter_valor_br(serie: pd.Series) -> pd.Series:
    """Converte texto no padrão brasileiro ("1.234,56") em número (1234.56).

    Remove o separador de milhar (ponto) e troca a vírgula decimal por ponto.
    errors="raise": se aparecer um valor que não é número, o ETL para e avisa,
    em vez de virar NaN silenciosamente.
    """
    texto = serie.astype(str).str.strip().str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="raise")


def tratar_supressao(serie: pd.Series) -> pd.DataFrame:
    """Separa o número de operações da marcação de sigilo (-1).

    Retorna duas colunas:
    - numero_operacoes: valor válido para somar (o -1 vira 0);
    - operacao_suprimida: 1 quando a combinação foi suprimida pelo BCB, 0 caso contrário.
    """
    operacoes = pd.to_numeric(serie, errors="raise").astype("int64")
    if (operacoes < -1).any():
        raise ValueError("numero_de_operacoes tem valor negativo diferente de -1 (não previsto pela metodologia).")
    return pd.DataFrame(
        {
            "numero_operacoes": operacoes.where(operacoes >= 0, 0),
            "operacao_suprimida": (operacoes == -1).astype("int64"),
        },
        index=serie.index,
    )


def relatorio_qualidade(df_bruto: pd.DataFrame) -> dict:
    """Mede a qualidade do arquivo bruto de um mês, antes de qualquer limpeza."""
    return {
        "ano_mes": str(df_bruto["data_base"].iloc[0])[:7],
        "linhas": int(len(df_bruto)),
        "nulos": int(df_bruto.isna().sum().sum()),
        "duplicadas": int(df_bruto.duplicated().sum()),
        "combinacoes_suprimidas": int((df_bruto["numero_de_operacoes"].astype(str).str.strip() == "-1").sum()),
    }


def limpar_mes(df_bruto: pd.DataFrame) -> pd.DataFrame:
    """Aplica as regras de limpeza a um mês e devolve só as colunas usadas na análise."""
    faltando = [c for c in COLUNAS_BRUTAS_NECESSARIAS if c not in df_bruto.columns]
    if faltando:
        raise ValueError(f"Colunas obrigatórias ausentes no arquivo do BCB: {faltando}")

    df = df_bruto[COLUNAS_BRUTAS_NECESSARIAS].drop_duplicates().copy()

    for coluna in config.COLUNAS_CATEGORICAS:
        df[coluna] = (
            df[coluna].fillna("Não informado").astype(str)
            .str.strip().str.replace(r"\s+", " ", regex=True)
        )

    # data_base vem como "2025-12-31"; a análise é mensal, então guardamos "2025-12".
    df["ano_mes"] = df["data_base"].astype(str).str[:7]

    for coluna in config.COLUNAS_MONETARIAS:
        df[coluna] = converter_valor_br(df[coluna])

    supressao = tratar_supressao(df["numero_de_operacoes"])
    df["numero_operacoes"] = supressao["numero_operacoes"]
    df["operacao_suprimida"] = supressao["operacao_suprimida"]

    df["grupo_credito"] = df["origem"].map(config.GRUPO_POR_ORIGEM)
    desconhecidas = df.loc[df["grupo_credito"].isna(), "origem"].unique().tolist()
    if desconhecidas:
        raise ValueError(f"Valor de origem não previsto: {desconhecidas}")

    df["regiao"] = df["uf"].map(config.REGIAO_POR_UF).fillna("Não informado")

    colunas_finais = [
        "ano_mes", "uf", "regiao", "cliente", "segmento", "cnae_ocupacao", "porte",
        "modalidade", "grupo_credito", "numero_operacoes", "operacao_suprimida",
        *config.COLUNAS_MONETARIAS,
    ]
    return df[colunas_finais].reset_index(drop=True)
