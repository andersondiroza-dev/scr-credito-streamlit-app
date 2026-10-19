"""Página central: responde a pergunta do projeto (crescimento vem com risco?)."""
import streamlit as st

from src import analysis, graficos, interface, utils

dados, filtros, fato = interface.contexto()
mes_base, mes_ref = interface.meses_comparacao(dados["fato_credito"], filtros)
st.title("Crescimento x Risco")
st.markdown(f"Cada ponto é um segmento de crédito. Comparação: **{utils.nome_mes(mes_base)} → {utils.nome_mes(mes_ref)}**.")
interface.aviso_filtros(filtros, fato)
if interface.sem_dados(fato):
    st.stop()

niveis = {
    "Instituição × modalidade × cliente": ("segmento", "modalidade", "cliente"),
    "Instituição × modalidade": ("segmento", "modalidade"),
    "Modalidade × cliente": ("modalidade", "cliente"),
    "UF": ("uf",),
}
c1, c2 = st.columns(2)
nivel = c1.selectbox("O que é cada ponto", list(niveis))
minimo_bi = c2.select_slider("Carteira mínima no mês base (R$ bi)", options=[0.1, 0.5, 1, 5, 10], value=1,
                             help="Exclui segmentos muito pequenos, em que pequenas variações viram percentuais enormes.")
chaves = niveis[nivel]
cxr = analysis.crescimento_x_risco(fato, mes_base, mes_ref, chaves=chaves, carteira_minima=minimo_bi * 1e9)

if cxr.empty or mes_base == mes_ref:
    st.info("Não há segmentos suficientes para comparar. Amplie o período (ao menos 2 meses) ou reduza a carteira mínima.")
    st.stop()

interface.mostrar(
    graficos.quadrante(cxr, cor=chaves[0]),
    "à direita da linha tracejada vertical estão os segmentos que cresceram mais que a mediana; acima da horizontal, "
    "os de inadimplência maior que a mediana. O quadrante superior direito concentra 'crescimento com risco'. "
    "O tamanho do ponto é a carteira. Passe o mouse para ver os detalhes.",
)

corr = analysis.correlacao_spearman(cxr, "crescimento_pct", "variacao_inadimplencia_pp")
st.subheader("O crescimento anda junto com a piora da inadimplência?")
c1, c2, c3 = st.columns(3)
c1.metric("Correlação de Spearman (ρ)", utils.numero_br(corr["rho"]))
c2.metric("p-valor", utils.numero_br(corr["p_valor"], 3))
c3.metric("Segmentos comparados", corr["n"])
st.markdown(analysis.interpretar_spearman(corr["rho"], corr["p_valor"]))
st.caption("Spearman compara a ordem dos valores (de -1 a +1). É robusto a crescimentos extremos e não supõe relação linear. "
           "Associação não é causa: crescer não 'provoca' inadimplência, e outros fatores (juros, perfil do cliente, prazo) influenciam. "
           "Atenção ao efeito denominador: carteiras que crescem muito rápido têm muitos contratos novos, que ainda não tiveram "
           "tempo de atrasar, o que pode reduzir a taxa no curto prazo.")

with st.expander("Tabela dos segmentos"):
    tabela = cxr.sort_values("carteira_ativa_ref", ascending=False).assign(
        carteira_ativa_ref=lambda d: d["carteira_ativa_ref"].map(utils.formatar_reais),
        crescimento_pct=lambda d: d["crescimento_pct"].map(utils.formatar_pct),
        inadimplencia_ref_pct=lambda d: d["inadimplencia_ref_pct"].map(utils.formatar_pct),
        variacao_inadimplencia_pp=lambda d: d["variacao_inadimplencia_pp"].map(utils.formatar_pp),
    )[list(chaves) + ["carteira_ativa_ref", "crescimento_pct", "inadimplencia_ref_pct", "variacao_inadimplencia_pp"]]
    tabela.columns = [c.capitalize() for c in chaves] + ["Carteira", "Crescimento", "Inadimplência", "Variação da inadimplência"]
    st.dataframe(tabela, hide_index=True, width="stretch")
