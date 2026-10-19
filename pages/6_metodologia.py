"""Fonte, método, decisões de tratamento e limites da análise."""
import streamlit as st

from src import config, interface, utils

dados, filtros, fato = interface.contexto()
st.title("Metodologia e limites")

st.markdown(f"""
### Fonte
- **SCR.data**, Painel de Operações de Crédito do Sistema de Informações de Crédito, publicado pelo **Banco Central do Brasil**.
- Página oficial: {config.URL_DATASET}
- Licença: **Open Data Commons Open Database License (ODbL)**. Período analisado: **jan/2024 a dez/2025** (24 meses).
- Obtenção: download dos arquivos públicos anuais (`scrdata_2024.zip`, `scrdata_2025.zip`) por `src/extract.py`.

### Como os dados foram tratados
1. Valores no padrão brasileiro (`1.234,56`) convertidos para número.
2. `numero_de_operacoes = -1` é **supressão por sigilo** do BCB (combinações com poucas operações): conta como 0 na soma e é registrada à parte.
3. Espaços normalizados; duplicadas exatas removidas; categoria ausente vira "Não informado".
4. Crédito **Livre/Direcionado** vem do campo oficial `origem` (sem/com destinação específica).
5. Colunas desnecessárias à pergunta (faixas de vencimento, indexador, submodalidade) foram descartadas.
6. Validação: a carteira nacional de dez/2025 confere com o arquivo bruto (R$ 7,444 tri, desvio de 0,00%).

### Indicadores
- **Inadimplência** = carteira vencida há mais de 90 dias ÷ carteira ativa.
- **Crescimento** = variação da carteira ativa entre o mês base (12 meses antes do fim do período, quando disponível) e o mês final.
- **HHI** = soma dos quadrados das participações de mercado (0 a 10.000).
- **Spearman** = correlação entre o crescimento e a variação da inadimplência dos segmentos.

### Limites (leia antes de concluir)
- Os dados são **agregados**: não há informação de clientes ou contratos individuais, nem de instituições específicas.
- A supressão por sigilo esconde o número de operações de cerca de 27% das combinações (o saldo continua somado).
- **Quebra em jan/2025:** a inadimplência subiu 0,31 p.p. em um único mês, cinco vezes a maior alta mensal de 2024. O mês coincide com a entrada em vigor da Resolução CMN 4.966/2021, que mudou regras contábeis de classificação de risco. É uma **hipótese** (não testada): parte da alta pode ser mudança de mensuração. Por isso, comparações dez/2024 → dez/2025 devem ser lidas com cautela.
- 24 meses é uma série curta: tendências descrevem o período e **não são previsões**.
- As análises mostram **associações**, não causas.
""")

st.subheader("Qualidade dos arquivos brutos (por mês)")
st.dataframe(
    dados["qualidade_mensal"].rename(columns={"ano_mes": "Mês", "linhas": "Linhas", "nulos": "Valores nulos",
                                              "duplicadas": "Linhas duplicadas", "combinacoes_suprimidas": "Combinações suprimidas (sigilo)"}),
    hide_index=True, width="stretch",
)
st.caption(utils.FONTE + ". Dicionário de dados completo em `docs/dicionario_dados.md` no repositório.")
