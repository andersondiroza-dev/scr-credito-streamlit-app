"""Tipos de instituição: participação de mercado, concentração, crescimento e risco."""
import streamlit as st

from src import analysis, graficos, interface, utils

dados, filtros, fato = interface.contexto()
mes_base, mes_ref = interface.meses_comparacao(dados["fato_credito"], filtros)
st.title("Quem empresta")
interface.aviso_filtros(filtros, fato)
if interface.sem_dados(fato):
    st.stop()

part, hhi = analysis.participacao_e_hhi(fato, mes_ref)
st.metric(f"Concentração do mercado (HHI, {utils.nome_mes(mes_ref)})", utils.numero_br(hhi, 0),
          help="Índice de Herfindahl-Hirschman: soma dos quadrados das participações, de 0 a 10.000.")
st.markdown(f"Resultado: **{analysis.classificar_hhi(hhi)}**.")

log = st.toggle("Escala logarítmica", value=True, help="Útil porque os bancos são muito maiores que os demais.")
interface.mostrar(
    graficos.barras(part, "segmento", "participacao_pct", f"Participação na carteira ativa ({utils.nome_mes(mes_ref)})",
                    "% da carteira", log=log),
    "quanto da carteira total cada tipo de instituição detém. Na escala logarítmica, cada marca do eixo vale 10 vezes a anterior.",
)

seg = analysis.crescimento_x_risco(fato, mes_base, mes_ref, chaves=("segmento",), carteira_minima=0)
if mes_base != mes_ref and not seg.empty:
    c1, c2 = st.columns(2)
    with c1:
        interface.mostrar(
            graficos.barras(seg.sort_values("crescimento_pct", ascending=False), "segmento", "crescimento_pct",
                            f"Crescimento ({utils.nome_mes(mes_base)} → {utils.nome_mes(mes_ref)})", "Crescimento (%)"),
            "variação percentual da carteira de cada tipo de instituição no período.",
        )
    with c2:
        interface.mostrar(
            graficos.barras(seg.sort_values("inadimplencia_ref_pct", ascending=False), "segmento", "inadimplencia_ref_pct",
                            f"Inadimplência em {utils.nome_mes(mes_ref)}", "% da carteira"),
            "percentual da carteira em operações com alguma parcela em atraso acima de 90 dias.",
        )
st.caption("A classificação 'Fintech', 'Banco' etc. é a do próprio BCB no campo 'segmento' do SCR.data.")
