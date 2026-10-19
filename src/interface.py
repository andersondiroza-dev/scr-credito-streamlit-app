"""Componentes compartilhados pelas páginas do app (carga de dados, filtros, avisos)."""
import pandas as pd
import streamlit as st

from src import analysis, config, utils

ARQUIVOS = {
    "fato_credito": "fato_credito.parquet",
    "fato_setor": "fato_setor.parquet",
    "resumo_mensal": "resumo_mensal.parquet",
    "qualidade_mensal": "qualidade_mensal.parquet",
}


@st.cache_data(show_spinner="Carregando dados do SCR.data...")
def _ler_parquet(caminho: str) -> pd.DataFrame:
    """Cache: o arquivo é lido uma vez e reaproveitado em todas as interações."""
    return pd.read_parquet(caminho)


def carregar_dados() -> dict:
    """Lê os Parquets. Se algum faltar, explica como gerá-lo e interrompe a página."""
    faltando = [nome for nome in ARQUIVOS.values() if not (config.DIR_PROCESSED / nome).exists()]
    if faltando:
        st.error(
            "Dados preparados não encontrados: " + ", ".join(faltando) + ". "
            "Gere-os com `python -m src.extract` e depois `python -m src.transform`."
        )
        st.stop()
    return {chave: _ler_parquet(str(config.DIR_PROCESSED / nome)) for chave, nome in ARQUIVOS.items()}


def _opcoes(fato: pd.DataFrame, coluna: str) -> list:
    return sorted(fato[coluna].astype(str).unique().tolist())


def barra_lateral(fato: pd.DataFrame) -> dict:
    """Filtros globais. Vazio = todos. Valem para todas as páginas."""
    st.sidebar.header("Filtros")
    meses = sorted(fato["ano_mes"].astype(str).unique().tolist())
    inicio, fim = st.sidebar.select_slider("Período", options=meses, value=(meses[0], meses[-1]), format_func=utils.nome_mes)
    clientes = st.sidebar.multiselect("Tipo de cliente", _opcoes(fato, "cliente"), placeholder="Todos",
                                      help="PF = pessoa física · PJ = pessoa jurídica")
    segmentos = st.sidebar.multiselect("Tipo de instituição", _opcoes(fato, "segmento"), placeholder="Todos",
                                       help="Classificação do próprio BCB no campo 'segmento' do SCR.data.")
    regioes = st.sidebar.multiselect("Região", _opcoes(fato, "regiao"), placeholder="Todas")
    ufs_disponiveis = _opcoes(fato[fato["regiao"].isin(regioes)] if regioes else fato, "uf")
    ufs = st.sidebar.multiselect("UF", ufs_disponiveis, placeholder="Todas")
    modalidades = st.sidebar.multiselect("Modalidade", _opcoes(fato, "modalidade"), placeholder="Todas")
    st.sidebar.caption(utils.FONTE)
    return {"inicio": inicio, "fim": fim, "clientes": clientes, "segmentos": segmentos,
            "regioes": regioes, "ufs": ufs, "modalidades": modalidades}


def contexto():
    """Usado pelas páginas: devolve (dados, filtros, fato já filtrado)."""
    dados, filtros = st.session_state["dados"], st.session_state["filtros"]
    fato = analysis.filtrar(dados["fato_credito"], **filtros)
    return dados, filtros, fato


def meses_comparacao(fato: pd.DataFrame, filtros: dict) -> tuple[str, str]:
    """(mês base, mês de referência) usados nos cálculos de crescimento."""
    meses = sorted(fato["ano_mes"].astype(str).unique().tolist())
    return analysis.mes_base_comparacao(meses, filtros["inicio"], filtros["fim"]), filtros["fim"]


def aviso_filtros(filtros: dict, fato_filtrado: pd.DataFrame) -> None:
    """Mostra o recorte ativo, como pede o enunciado (filtros e quantidade de dados exibidos)."""
    partes = [f"{utils.nome_mes(filtros['inicio'])} a {utils.nome_mes(filtros['fim'])}"]
    nomes = {"clientes": "Cliente", "segmentos": "Instituição", "regioes": "Região", "ufs": "UF", "modalidades": "Modalidade"}
    partes += [f"{rotulo}: {', '.join(filtros[chave])}" for chave, rotulo in nomes.items() if filtros[chave]]
    quantidade = f"{len(fato_filtrado):,}".replace(",", ".")
    st.caption("**Filtros ativos:** " + " · ".join(partes) + f" · **{quantidade} combinações de dados**")


def sem_dados(df: pd.DataFrame) -> bool:
    if df.empty:
        st.info("Nenhum dado para os filtros escolhidos. Amplie o período ou remova algum filtro na barra lateral.")
        return True
    return False


def mostrar(fig, como_ler: str) -> None:
    # theme=None mantém a paleta e o layout definidos em src/graficos.py (o tema do Streamlit os substituiria)
    st.plotly_chart(fig, width="stretch", theme=None)
    st.caption(f"**Como ler:** {como_ler}")
