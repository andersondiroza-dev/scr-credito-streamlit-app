"""Indicadores e estatísticas do projeto.

Este módulo é a "fonte única da verdade" dos números: o notebook de EDA e o app
Streamlit chamam as mesmas funções, então um número nunca difere entre os dois.
"""
import numpy as np
import pandas as pd
from scipy import stats

METRICAS = ["carteira_ativa", "carteira_inadimplencia", "ativo_problematico", "numero_operacoes"]


def taxa_percentual(numerador, denominador):
    """numerador / denominador × 100, devolvendo NaN (e não erro) quando o denominador é 0."""
    if np.isscalar(denominador):
        return float("nan") if denominador == 0 else float(numerador) / float(denominador) * 100
    return numerador / denominador.replace(0, np.nan) * 100


def filtrar(fato, inicio, fim, clientes=None, segmentos=None, regioes=None, ufs=None, modalidades=None):
    """Aplica os filtros da barra lateral. Lista vazia ou None significa "todos"."""
    mascara = (fato["ano_mes"] >= inicio) & (fato["ano_mes"] <= fim)
    for coluna, valores in [("cliente", clientes), ("segmento", segmentos), ("regiao", regioes), ("uf", ufs), ("modalidade", modalidades)]:
        if valores:
            mascara &= fato[coluna].isin(valores)
    return fato[mascara]


def mes_base_comparacao(meses, inicio, fim):
    """Mês de comparação para o crescimento: 12 meses antes do fim, se estiver no período.

    Comparar sempre o mesmo mês (dez contra dez) evita confundir crescimento com
    sazonalidade. Se o período escolhido for menor que 12 meses, usa o início do período.
    """
    candidato = f"{int(fim[:4]) - 1}-{fim[5:7]}"
    return candidato if candidato >= inicio and candidato in meses else inicio


def serie_mensal(fato, por=None):
    """Soma as métricas por mês (e por grupo, se `por` for informado) e calcula as taxas."""
    chaves = ["ano_mes"] + ([por] if por else [])
    serie = fato.groupby(chaves, as_index=False, observed=True)[METRICAS].sum()
    serie["taxa_inadimplencia"] = taxa_percentual(serie["carteira_inadimplencia"], serie["carteira_ativa"])
    serie["taxa_ativo_problematico"] = taxa_percentual(serie["ativo_problematico"], serie["carteira_ativa"])
    return serie.sort_values(chaves).reset_index(drop=True)


def kpis(fato, mes_base, mes_ref):
    """Os 4 números principais da página Início."""
    base = fato[fato["ano_mes"] == mes_base]
    ref = fato[fato["ano_mes"] == mes_ref]
    carteira_base = float(base["carteira_ativa"].sum())
    carteira_ref = float(ref["carteira_ativa"].sum())
    return {
        "carteira_base": carteira_base,
        "carteira_ref": carteira_ref,
        "crescimento_pct": taxa_percentual(carteira_ref - carteira_base, carteira_base),
        "inadimplencia_base_pct": taxa_percentual(base["carteira_inadimplencia"].sum(), carteira_base),
        "inadimplencia_ref_pct": taxa_percentual(ref["carteira_inadimplencia"].sum(), carteira_ref),
        "participacao_fintech_pct": taxa_percentual(ref.loc[ref["segmento"] == "Fintech", "carteira_ativa"].sum(), carteira_ref),
    }
