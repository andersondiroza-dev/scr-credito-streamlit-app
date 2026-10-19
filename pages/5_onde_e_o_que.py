"""Recortes geográfico (UF) e de produto (modalidade, livre x direcionado)."""
import streamlit as st

from src import analysis, graficos, interface, utils

dados, filtros, fato = interface.contexto()
mes_base, mes_ref = interface.meses_comparacao(dados["fato_credito"], filtros)
st.title("Onde e o quê")
interface.aviso_filtros(filtros, fato)
if interface.sem_dados(fato):
    st.stop()

aba_uf, aba_produto = st.tabs(["Por UF", "Por produto"])

with aba_uf:
    uf = analysis.crescimento_x_risco(fato, mes_base, mes_ref, chaves=("uf",), carteira_minima=0)
    if mes_base != mes_ref and not uf.empty:
        interface.mostrar(
            graficos.barras(uf.sort_values("inadimplencia_ref_pct", ascending=False), "uf", "inadimplencia_ref_pct",
                            f"Inadimplência por UF ({utils.nome_mes(mes_ref)})", "% da carteira", horizontal=False),
            "UFs ordenadas da maior para a menor inadimplência.",
        )
    mensal_uf = analysis.serie_mensal(fato, por="uf")
    interface.mostrar(
        graficos.boxplot(mensal_uf, "uf", "Distribuição da inadimplência mensal por UF"),
        "cada caixa resume os meses do período: a linha central é a mediana, a caixa vai do 1º ao 3º quartil "
        "e os pontos isolados são meses atípicos. Caixa alta = inadimplência que oscilou muito.",
    )
    with st.expander("Estatísticas descritivas por UF"):
        st.dataframe(analysis.descritivas_por_grupo(fato, "uf").round(2), width="stretch")

with aba_produto:
    mod = analysis.crescimento_x_risco(fato, mes_base, mes_ref, chaves=("modalidade",), carteira_minima=0)
    if mes_base != mes_ref and not mod.empty:
        mod = mod.assign(carteira_bi=mod["carteira_ativa_ref"] / 1e9)
        interface.mostrar(
            graficos.barras(mod.sort_values("carteira_bi", ascending=False), "modalidade", "carteira_bi",
                            f"Carteira por modalidade ({utils.nome_mes(mes_ref)})", "R$ bilhões"),
            "tamanho de cada tipo de operação de crédito.",
        )
        interface.mostrar(
            graficos.barras(mod.sort_values("inadimplencia_ref_pct", ascending=False), "modalidade", "inadimplencia_ref_pct",
                            f"Inadimplência por modalidade ({utils.nome_mes(mes_ref)})", "% da carteira"),
            "modalidades com maior parcela em atraso acima de 90 dias. 'Adiantamentos a depositantes' (cheque especial "
            "sem limite) é pequena em saldo, mas tem inadimplência muito alta.",
        )
    grupo = analysis.serie_mensal(fato, por="grupo_credito")
    interface.mostrar(
        graficos.linhas_mensais(grupo, "taxa_inadimplencia", "Inadimplência: crédito livre x direcionado", "% da carteira",
                                por="grupo_credito", marcar_jan_2025=True),
        "crédito direcionado (rural, imobiliário, BNDES) tem regras e juros próprios; o livre é negociado entre as partes.",
    )
