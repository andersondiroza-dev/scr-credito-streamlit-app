# Especificação do Projeto: Panorama do Crédito Nacional (SCR.data) em Streamlit

> Documento de design aprovado em 19/10/2026. Ele guia a implementação do Projeto Final
> do curso Visualização de Dados e BI (SENAI SC / SCTEC, Módulo 2, Semana 13).
> Prazo de entrega: **30/10/2026 às 22h**, considerando o último commit no GitHub.

## 1. Problema, pergunta e público

**Pergunta orientadora:** onde o crédito brasileiro está crescendo entre 2024 e 2025, e
esse crescimento vem acompanhado de mais risco?

**Público:** gestores de risco, analistas de crédito e tomadores de decisão em fintechs
e instituições financeiras.

**Relevância:** crescer a carteira sem controlar a inadimplência destrói valor. Saber em
quais segmentos (tipo de instituição, modalidade, PF/PJ, UF) o crescimento é "saudável"
e em quais ele vem com risco ajuda a priorizar a concessão e o monitoramento.

**Contexto profissional:** o mesmo dataset sustenta um case comercial do autor
(bcb-scr-data.andersondiroza.com.br), feito em outra stack (Lovable). Ele já gerou
contratos e o interesse de fintechs. Este projeto refaz todo o pipeline em Python +
Streamlit, conforme aprovado pelo professor Rodrigo Brunini em 11/10/2026.

**Dentro do escopo:**
- carteira, inadimplência e ativo problemático, de jan/2024 a dez/2025
- recortes nacionais por PF/PJ, tipo de instituição, modalidade, porte, UF e região

**Fora do escopo:**
- dados individuais de pessoas ou de instituições (o SCR.data é agregado)
- previsão ou modelagem preditiva
- séries anteriores a 2024
- explicações causais

**Critérios de conclusão:**
- ETL reproduzível a partir das URLs oficiais
- EDA documentada com as quatro análises da seção 4
- app publicado no Streamlit Community Cloud, com os filtros funcionando
- README com as 16 seções obrigatórias

## 2. Fonte de dados

| Item | Valor |
|---|---|
| Fonte | SCR.data: Painel de Operações de Crédito (Sistema de Informações de Crédito) |
| Publicador | Banco Central do Brasil (BCB/Desig) |
| Página | https://dadosabertos.bcb.gov.br/dataset/scr_data |
| Arquivos | `https://www.bcb.gov.br/pda/desig/scrdata_2024.zip` e `scrdata_2025.zip` (12 CSVs mensais cada) |
| Licença | Open Data Commons Open Database License (ODbL), conferida via API CKAN em 19/10/2026 |
| Método | download de arquivo público oficial (o portal não tem API de consulta filtrada) |
| Período | 2024-01 a 2025-12 (24 meses) |
| Formato bruto | CSV `;`, UTF-8 com BOM, números no formato brasileiro `1.234,56` |
| Privacidade | dados agregados; o BCB suprime células pequenas (`numero_de_operacoes = -1`) para evitar reidentificação |

## 3. Arquitetura e fluxo (Caminho A: pipeline completo com Parquet versionado)

```
scr-credito-streamlit/
├── app.py                    # entrada do Streamlit (página Início)
├── pages/                    # demais páginas do app
├── src/
│   ├── config.py             # caminhos relativos, URLs, período
│   ├── extract.py            # baixa os ZIPs (pula se já existirem)
│   ├── transform.py          # limpeza, tipos, agregação -> Parquet
│   ├── analysis.py           # indicadores e estatísticas
│   └── utils.py              # formatação (R$, %), mensagens
├── notebooks/01_eda.ipynb
├── data/raw/                 # ZIPs (ignorado pelo Git)
├── data/processed/           # Parquets (versionados)
├── outputs/                  # imagens para o README
├── docs/                     # esta especificação + dicionario_dados.md
├── tests/                    # pytest
├── .streamlit/config.toml    # tema azul/branco
├── README.md  requirements.txt  .gitignore  .env.example
```

**Fluxo:**
1. `python -m src.extract` baixa os ZIPs para `data/raw/`.
2. `python -m src.transform` grava `data/processed/*.parquet`.
3. `streamlit run app.py` abre o app, que **apenas lê** os Parquets.

### Decisões de tratamento (registradas no código e no README)
1. Valores monetários `1.234,56`: removo `.` e troco `,` por `.`, convertendo para float.
2. `numero_de_operacoes = -1` é supressão por sigilo, não erro. Na soma vira 0, e a
   quantidade de combinações suprimidas é contada em uma coluna própria.
3. Faço `strip` nas categorias e verifico valores ausentes e linhas duplicadas, com um
   relatório impresso no console.
4. `grupo_credito` (Livre/Direcionado) vem do campo oficial `origem`: "Sem destinação
   específica" vira Livre e "Com destinação específica" vira Direcionado. É a classificação
   do próprio BCB, sem aproximação. A submodalidade não entra no fato, o que reduz o volume.
5. Minimização (enunciado 4.4): as faixas de vencimento ("a vencer até 90 dias" etc.) e o
   indexador não respondem à pergunta e são descartados. Espaços duplicados nas categorias
   são normalizados.
6. Linhas duplicadas exatas são removidas, com a contagem registrada. Categorias ausentes
   viram "Não informado". Valor monetário que não converte interrompe o ETL com erro.
7. Validação: a carteira ativa nacional de dez/2025 deve ser ≈ R$ 7,444 tri (conferido no
   arquivo bruto em 19/10/2026). Se divergir mais de 1%, o ETL falha.

### Saídas
- `fato_credito`: ano_mes × uf × regiao × cliente × segmento × modalidade × grupo_credito
  × porte, com as métricas monetárias e as operações. A região é uma coluna, não uma
  tabela à parte.
- `fato_setor`: ano_mes × cliente × cnae_ocupacao
- `resumo_mensal`: ano_mes × cliente
- `qualidade_mensal`: linhas, nulos, duplicadas e supressões por mês (alimenta a EDA)

## 4. Análise e estatística (`src/analysis.py` + notebook)

**Indicadores:**
- carteira ativa (R$)
- crescimento em 12 meses (dez/25 vs dez/24)
- taxa de inadimplência = `carteira_inadimplencia` (saldo das operações com alguma parcela em atraso > 90 dias, conforme a metodologia do BCB) ÷ `carteira_ativa`
- % de ativo problemático
- participação de mercado por segmento e HHI

**Análises:**
1. **Descritivas por grupo:** média, mediana, desvio-padrão e quartis da inadimplência
   mensal por UF, modalidade e segmento; boxplot das 27 UFs.
2. **Correlação de Spearman** entre o crescimento em 12 meses e a variação da
   inadimplência (em pontos percentuais), por combinação segmento × modalidade × cliente,
   com p-valor e ressalva de causalidade. Spearman foi escolhido por ser robusto a outliers.
   Combinações com carteira muito pequena são excluídas, com o limite documentado.
3. **Tendência:** regressão linear (`scipy.stats.linregress`) da inadimplência mensal,
   com a inclinação, o IC 95% e a ressalva de série curta.
4. **Quadrante de risco:** dispersão com crescimento × inadimplência, em que o tamanho
   do ponto é a carteira.

A conclusão do notebook separa **observação**, **hipótese** e **recomendação**.

## 5. App Streamlit

- **Barra lateral:**
  - filtros de período, PF/PJ, segmento, região/UF e modalidade
  - aviso "Filtros ativos … · N combinações"
- **Páginas:**
  1. Início: pergunta, público, contexto comercial, 4 KPIs e 3 achados
  2. Evolução
  3. Crescimento x Risco
  4. Quem empresta
  5. Onde e o quê
  6. Metodologia e limites
- **Gráficos (Plotly):** título, eixos com unidade, legenda, rodapé "Fonte: BCB – SCR.data"
  e ajuda "como ler".
- **Erros:** filtro sem dados mostra `st.info` amigável; Parquet ausente mostra a
  instrução do ETL; carregamento usa `st.cache_data`.
- **Visual:** azul/branco, em português do Brasil.

## 6. Qualidade, versionamento e entrega

- **Testes (`pytest`):**
  - conversão de dinheiro
  - tratamento de supressão
  - fórmula da inadimplência
  - validação do total
- **Git:**
  - `main` estável e `develop`, com branches `feature/etl`, `feature/eda`, `feature/app`
    e `docs/readme`
  - commits pequenos no imperativo em PT; repositório **privado** no GitHub, com o
    professor como colaborador
- **Ambiente:** `.venv`; `requirements.txt` (só o que o app usa no deploy) e
  `requirements-dev.txt` (pytest, Jupyter, Matplotlib), ambos com versões fixas. O
  Streamlit Cloud é configurado com Python 3.12.
- **Navegação:** `st.navigation` no `app.py`, com as páginas em `pages/`. Os filtros da
  barra lateral são definidos uma única vez, no `app.py`.
- **Responsabilidades do autor:**
  - Trello
  - vídeo de ≤ 3 min no LinkedIn marcando @rgbrunini, LAB365, SENAI SC e FIESC
  - vídeo também no Google Drive com acesso de leitor por link
  - publicação no repositório da turma
  - links no AVA
  - **não fazer commits depois da entrega**

## 7. Cronograma

| Data | Etapa |
|---|---|
| 19–20/10 | estrutura, extract, transform, testes, Parquets |
| 21–22/10 | analysis + notebook EDA |
| 23–24/10 | app Streamlit + deploy |
| 25–26/10 | README, dicionário, revisão; roteiro do vídeo e cards do Trello |
| 27/10 | gravação do vídeo |
| 28/10 | publicações e envio no AVA (2 dias de folga) |
