"""Página Início: pergunta, público, contexto e os principais números."""
import streamlit as st

from src import analysis, interface, utils

dados, filtros, fato = interface.contexto()
mes_base, mes_ref = interface.meses_comparacao(dados["fato_credito"], filtros)

st.title("Panorama do Crédito Nacional")
st.markdown(
    "**Pergunta:** onde o crédito brasileiro está crescendo entre 2024 e 2025, "
    "e esse crescimento vem acompanhado de mais risco?\n\n"
    "**Para quem:** gestores de risco, analistas de crédito e tomadores de decisão em fintechs e instituições financeiras."
)

st.info(
    "**Resposta (base completa, dez/2024 → dez/2025):** o crédito cresceu **11,30%** e a inadimplência subiu de "
    "**2,99% para 4,10%**. A piora, porém, foi **generalizada**: os segmentos que mais cresceram não foram os que "
    "mais pioraram (correlação de Spearman ρ = 0,12, p = 0,43, sem significância estatística). "
    "Detalhes na página *Crescimento x Risco* e no notebook de EDA do repositório."
)

interface.aviso_filtros(filtros, fato)
if interface.sem_dados(fato):
    st.stop()

k = analysis.kpis(fato, mes_base, mes_ref)
comparacao = f"{utils.nome_mes(mes_base)} → {utils.nome_mes(mes_ref)}"
st.subheader(f"Indicadores do recorte filtrado ({comparacao})")
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Carteira ativa ({utils.nome_mes(mes_ref)})", utils.formatar_reais(k["carteira_ref"]),
          help="Saldo total das operações de crédito, em dia e em atraso.")
c2.metric("Crescimento da carteira", utils.formatar_pct(k["crescimento_pct"]), help=f"Comparação {comparacao}.")
c3.metric("Inadimplência (> 90 dias)", utils.formatar_pct(k["inadimplencia_ref_pct"]),
          delta=utils.formatar_pp(k["inadimplencia_ref_pct"] - k["inadimplencia_base_pct"]), delta_color="inverse",
          help=f"Parcela da carteira vencida há mais de 90 dias. A seta mostra a variação {comparacao} (vermelho = piora).")
c4.metric("Participação das fintechs", utils.formatar_pct(k["participacao_fintech_pct"]),
          help="Fatia da carteira ativa concedida por instituições classificadas pelo BCB como Fintech.")

st.subheader("Principais achados no recorte atual")
por_cliente = analysis.crescimento_x_risco(fato, mes_base, mes_ref, chaves=("cliente",), carteira_minima=0)
por_segmento = analysis.crescimento_x_risco(fato, mes_base, mes_ref, chaves=("segmento",), carteira_minima=0)
achados = [f"A carteira variou **{utils.formatar_pct(k['crescimento_pct'])}** ({comparacao}), chegando a "
           f"**{utils.formatar_reais(k['carteira_ref'])}**."]
if len(por_cliente) == 2:
    pf, pj = (por_cliente.set_index("cliente").loc[c, "inadimplencia_ref_pct"] for c in ("PF", "PJ"))
    comparativo = "maior que" if pf > pj else "menor que"
    achados.append(f"A inadimplência de pessoa física (**{utils.formatar_pct(pf)}**) é {comparativo} a de pessoa jurídica "
                   f"(**{utils.formatar_pct(pj)}**) em {utils.nome_mes(mes_ref)}.")
if mes_base != mes_ref and not por_segmento.empty:
    lider = por_segmento.sort_values("crescimento_pct", ascending=False).iloc[0]
    achados.append(f"O tipo de instituição que mais cresceu foi **{lider['segmento']}** "
                   f"(**{utils.formatar_pct(lider['crescimento_pct'])}**), com inadimplência de "
                   f"**{utils.formatar_pct(lider['inadimplencia_ref_pct'])}** em {utils.nome_mes(mes_ref)}.")
for achado in achados:
    st.markdown(f"- {achado}")

with st.expander("Por que este painel existe (aplicação profissional)"):
    st.markdown(
        "Este painel usa o mesmo conjunto de dados de um case comercial do autor, publicado em outra tecnologia "
        "([bcb-scr-data.andersondiroza.com.br](https://bcb-scr-data.andersondiroza.com.br)). Ao ser apresentado "
        "em funcionamento, esse case gerou contratos com clientes de menor porte e contatos de duas fintechs e de "
        "uma financeira de cartões. Esta versão refaz todo o pipeline em Python e Streamlit, com o processo de "
        "dados documentado, testado e reproduzível."
    )

st.caption("Os resultados descrevem associações nos dados agregados do BCB e não demonstram causalidade. "
           "Veja a página *Metodologia e limites*.")
