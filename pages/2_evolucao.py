"""Evolução mensal da carteira e da inadimplência, com a tendência estatística."""
import streamlit as st

from src import analysis, graficos, interface, utils

dados, filtros, fato = interface.contexto()
st.title("Evolução mensal")
interface.aviso_filtros(filtros, fato)
if interface.sem_dados(fato):
    st.stop()

opcoes = {"Total": None, "Tipo de cliente (PF/PJ)": "cliente", "Tipo de instituição": "segmento",
          "Crédito livre x direcionado": "grupo_credito"}
escolha = st.radio("Separar as linhas por", list(opcoes), horizontal=True)
por = opcoes[escolha]
serie = analysis.serie_mensal(fato, por=por)

interface.mostrar(
    graficos.linhas_mensais(serie, "carteira_ativa", "Carteira ativa por mês", "R$ bilhões", por=por, escala=1e9),
    "cada ponto é o saldo total de crédito no fim do mês. Linha subindo = carteira crescendo.",
)
interface.mostrar(
    graficos.linhas_mensais(serie, "taxa_inadimplencia", "Taxa de inadimplência (> 90 dias) por mês", "% da carteira",
                            por=por, marcar_jan_2025=True),
    "percentual da carteira em operações com alguma parcela em atraso acima de 90 dias. Linha subindo = risco aumentando. "
    "A linha pontilhada marca jan/2025, quando a Res. CMN 4.966/2021 entrou em vigor e a série muda de comportamento.",
)

st.subheader("Tendência da inadimplência (regressão linear)")
st.markdown("A inclinação é a variação média por mês, em pontos percentuais. Como a série muda de comportamento em "
            "jan/2025, a tendência é calculada **no período todo e em cada ano separadamente**.")
total = analysis.serie_mensal(fato)
linhas = []
for rotulo, recorte in [("Período filtrado", total),
                        ("Somente 2024", total[total["ano_mes"].str.startswith("2024")]),
                        ("Somente 2025", total[total["ano_mes"].str.startswith("2025")])]:
    t = analysis.tendencia_linear(recorte["taxa_inadimplencia"])
    linhas.append({
        "Recorte": rotulo, "Meses": t["n"],
        "Variação média por mês": utils.formatar_pp(t["inclinacao"], 3),
        "IC 95%": f"{utils.formatar_pp(t['ic95_inferior'], 3)} a {utils.formatar_pp(t['ic95_superior'], 3)}",
        "R²": utils.numero_br(t["r2"]),
        "Significativa (p < 0,05)?": "n/d" if t["n"] < 3 else ("sim" if t["p_valor"] < 0.05 else "não"),
    })
st.dataframe(linhas, hide_index=True, width="stretch")
st.caption("Como ler: se o intervalo de confiança (IC 95%) não inclui zero, a tendência de alta ou de queda é consistente. "
           "Recortes com menos de 3 meses aparecem como n/d. Ressalva: séries de 12 a 24 meses são curtas; "
           "a reta descreve o período e não é previsão.")
