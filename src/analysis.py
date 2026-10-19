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
        if denominador == 0:
            return float("nan") if np.isscalar(numerador) else numerador * np.nan
        resultado = numerador / denominador * 100
        return float(resultado) if np.isscalar(numerador) else resultado
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


def crescimento_x_risco(fato, mes_base, mes_ref, chaves=("segmento", "modalidade", "cliente"), carteira_minima=1e9):
    """Para cada combinação (ex.: Fintech × Empréstimos × PF), mede quanto a carteira cresceu
    e quanto a inadimplência mudou entre os dois meses.

    carteira_minima (R$) exclui combinações muito pequenas, em que poucos reais de
    diferença geram percentuais enormes e distorcem a análise. Padrão: R$ 1 bilhão.
    """
    chaves = list(chaves)
    colunas = ["carteira_ativa", "carteira_inadimplencia"]
    base = fato[fato["ano_mes"] == mes_base].groupby(chaves, observed=True)[colunas].sum()
    ref = fato[fato["ano_mes"] == mes_ref].groupby(chaves, observed=True)[colunas].sum()
    df = base.join(ref, lsuffix="_base", rsuffix="_ref", how="inner")
    df = df[df["carteira_ativa_base"] >= max(carteira_minima, 0.01)]

    df["crescimento_pct"] = taxa_percentual(df["carteira_ativa_ref"] - df["carteira_ativa_base"], df["carteira_ativa_base"])
    df["inadimplencia_base_pct"] = taxa_percentual(df["carteira_inadimplencia_base"], df["carteira_ativa_base"])
    df["inadimplencia_ref_pct"] = taxa_percentual(df["carteira_inadimplencia_ref"], df["carteira_ativa_ref"])
    df["variacao_inadimplencia_pp"] = df["inadimplencia_ref_pct"] - df["inadimplencia_base_pct"]
    colunas_saida = chaves + ["carteira_ativa_base", "carteira_ativa_ref", "crescimento_pct",
                              "inadimplencia_base_pct", "inadimplencia_ref_pct", "variacao_inadimplencia_pp"]
    return df.reset_index()[colunas_saida]


def correlacao_spearman(df, x, y):
    """Correlação de Spearman entre duas colunas.

    Por que Spearman e não Pearson: ele compara a ORDEM dos valores (postos), não os
    valores em si. Assim, um crescimento explosivo (ex.: +300%) não domina o resultado,
    e não é preciso supor relação linear nem distribuição normal.
    """
    dados = df[[x, y]].dropna()
    n = int(len(dados))
    if n < 3:
        return {"rho": float("nan"), "p_valor": float("nan"), "n": n}
    resultado = stats.spearmanr(dados[x], dados[y])
    return {"rho": float(resultado.statistic), "p_valor": float(resultado.pvalue), "n": n}


def interpretar_spearman(rho, p_valor, alfa=0.05):
    """Traduz o resultado para linguagem simples, sem afirmar causalidade."""
    if np.isnan(rho):
        return "Não há combinações suficientes para calcular a correlação com os filtros atuais."
    if p_valor >= alfa:
        return (f"A correlação (ρ = {rho:.2f}) não é estatisticamente significativa (p = {p_valor:.3f}): "
                "não há evidência de que crescer mais ande junto com mais risco neste recorte.")
    forca = "forte" if abs(rho) >= 0.6 else "moderada" if abs(rho) >= 0.3 else "fraca"
    sentido = "positiva" if rho > 0 else "negativa"
    leitura = ("segmentos que mais cresceram tenderam a piorar mais a inadimplência" if rho > 0
               else "segmentos que mais cresceram tenderam a piorar menos (ou melhorar) a inadimplência")
    return (f"Correlação {sentido} {forca} (ρ = {rho:.2f}, p = {p_valor:.3f}): {leitura}. "
            "Correlação não implica causalidade.")


def tendencia_linear(valores):
    """Reta de tendência (mínimos quadrados) de uma série mensal.

    A inclinação é a variação média por mês (em p.p., se a série for uma taxa em %).
    O intervalo de confiança de 95% usa a distribuição t com n-2 graus de liberdade.
    """
    y = np.asarray(list(valores), dtype=float)
    n = len(y)
    if n < 3:
        return {"inclinacao": float("nan"), "ic95_inferior": float("nan"), "ic95_superior": float("nan"),
                "r2": float("nan"), "p_valor": float("nan"), "n": n}
    reta = stats.linregress(np.arange(n), y)
    margem = stats.t.ppf(0.975, n - 2) * reta.stderr
    return {
        "inclinacao": float(reta.slope),
        "ic95_inferior": float(reta.slope - margem),
        "ic95_superior": float(reta.slope + margem),
        "r2": float(reta.rvalue ** 2),
        "p_valor": float(reta.pvalue),
        "n": n,
    }


def participacao_e_hhi(fato, mes, por="segmento"):
    """Participação de mercado (%) e índice de Herfindahl-Hirschman (HHI).

    HHI = soma dos quadrados das participações em %, de 0 (pulverizado) a 10.000
    (um único participante). Mede o quanto o crédito está concentrado.
    """
    no_mes = fato[fato["ano_mes"] == mes]
    part = no_mes.groupby(por, as_index=False, observed=True)["carteira_ativa"].sum()
    part["participacao_pct"] = taxa_percentual(part["carteira_ativa"], part["carteira_ativa"].sum())
    part = part.sort_values("participacao_pct", ascending=False).reset_index(drop=True)
    hhi = float((part["participacao_pct"] ** 2).sum())
    return part, hhi


def classificar_hhi(hhi):
    """Faixas usadas por autoridades de concorrência (Guia do CADE / DOJ-FTC)."""
    if hhi < 1500:
        return "baixa concentração (HHI < 1.500)"
    if hhi <= 2500:
        return "moderada concentração (1.500 a 2.500)"
    return "alta concentração (HHI > 2.500)"


def descritivas_por_grupo(fato, grupo):
    """Estatísticas descritivas da taxa de inadimplência MENSAL de cada grupo.

    Cada grupo (ex.: cada UF) gera uma série de meses; resumimos essa série com medidas
    de centro (média, mediana), de dispersão (desvio-padrão, quartis) e extremos.
    """
    mensal = serie_mensal(fato, por=grupo)
    g = mensal.groupby(grupo, observed=True)["taxa_inadimplencia"]
    tabela = pd.DataFrame({
        "media": g.mean(), "mediana": g.median(), "desvio_padrao": g.std(),
        "q1": g.quantile(0.25), "q3": g.quantile(0.75),
        "minimo": g.min(), "maximo": g.max(), "n_meses": g.count(),
    })
    return tabela.sort_values("mediana", ascending=False)
