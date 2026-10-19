"""Gráficos Plotly do app. Todo gráfico sai com título, eixos com unidade, legenda e fonte."""
import plotly.express as px
import plotly.graph_objects as go

from src import utils

# Nome legível de cada coluna, usado nos títulos dos eixos.
ROTULOS = {"uf": "UF", "segmento": "Tipo de instituição", "modalidade": "Modalidade", "cliente": "Cliente",
           "grupo_credito": "Grupo de crédito", "regiao": "Região"}

PALETA = ["#1F4E9E", "#E07A1F", "#2E9E8F", "#B23A48", "#7FB3E6", "#0B2A5B", "#8C9BB0", "#C9A227"]


def _padronizar(fig: go.Figure, titulo: str, rotulo_x: str, rotulo_y: str) -> go.Figure:
    fig.update_layout(
        title=titulo, xaxis_title=rotulo_x, yaxis_title=rotulo_y,
        template="plotly_white", colorway=PALETA, margin=dict(t=90, b=110),
        separators=",.",  # padrão brasileiro nos eixos: vírgula decimal e ponto de milhar
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
    )
    # yshift em pixels mantém a fonte logo abaixo do eixo x, qualquer que seja a altura do gráfico
    fig.add_annotation(text=utils.FONTE, xref="paper", yref="paper", x=0, y=0, yanchor="top", yshift=-75,
                       showarrow=False, font=dict(size=10, color="#5B6B82"), xanchor="left")
    return fig


def linhas_mensais(serie, valor, titulo, rotulo_y, por=None, escala=1.0, marcar_jan_2025=False):
    """Série mensal. `escala` divide o valor (ex.: 1e9 para mostrar em R$ bilhões).

    marcar_jan_2025 desenha uma linha vertical no mês em que a Res. CMN 4.966/2021 entrou
    em vigor, porque a série de inadimplência muda de comportamento nesse ponto.
    """
    dados = serie.assign(_y=serie[valor] / escala, _mes=serie["ano_mes"].map(utils.nome_mes))
    if por:
        dados[por] = dados[por].astype(str)
    fig = px.line(dados, x="_mes", y="_y", color=por, markers=True, color_discrete_sequence=PALETA,
                  labels={"_y": rotulo_y, "_mes": "Mês", por or "": ""})
    fig = _padronizar(fig, titulo, "Mês", rotulo_y)
    if marcar_jan_2025 and "jan/2025" in dados["_mes"].values:
        # Linha e texto são adicionados separadamente: o Plotly não posiciona o texto
        # automático de add_vline quando o eixo x é de categorias (meses).
        fig.add_vline(x="jan/2025", line_dash="dot", line_color="gray")
        fig.add_annotation(x="jan/2025", y=1, yref="paper", text="jan/2025: Res. CMN 4.966 em vigor",
                           showarrow=False, xanchor="left", yanchor="top", font=dict(size=10, color="gray"))
    return fig


def quadrante(cxr, cor="segmento"):
    """Dispersão crescimento × inadimplência; as linhas tracejadas são as medianas."""
    rotulo = [c for c in ["segmento", "modalidade", "cliente", "uf"] if c in cxr.columns]
    dados = cxr.assign(_carteira_bi=cxr["carteira_ativa_ref"] / 1e9, **{c: cxr[c].astype(str) for c in rotulo})
    fig = px.scatter(
        dados, x="crescimento_pct", y="inadimplencia_ref_pct", size="_carteira_bi", color=cor, color_discrete_sequence=PALETA,
        hover_data={c: True for c in rotulo} | {"_carteira_bi": ":.1f", "variacao_inadimplencia_pp": ":.2f"},
        labels={"crescimento_pct": "Crescimento da carteira (%)", "inadimplencia_ref_pct": "Inadimplência (%)",
                "_carteira_bi": "Carteira (R$ bi)", "variacao_inadimplencia_pp": "Variação da inadimplência (p.p.)"},
        size_max=45,
    )
    fig.add_vline(x=dados["crescimento_pct"].median(), line_dash="dash", line_color="gray")
    fig.add_hline(y=dados["inadimplencia_ref_pct"].median(), line_dash="dash", line_color="gray")
    fig = _padronizar(fig, "Quadrante de risco: crescimento × inadimplência",
                      "Crescimento da carteira no período (%)", "Inadimplência no mês final (%)")
    # Legenda vertical à direita: com muitas categorias, a horizontal invadiria o título.
    fig.update_layout(height=560, legend=dict(orientation="v", x=1.02, y=1, yanchor="top", xanchor="left"))
    return fig


def barras(df, categoria, valor, titulo, rotulo_valor, horizontal=True, log=False):
    dados = df.assign(**{categoria: df[categoria].astype(str)})
    eixos = dict(x=valor, y=categoria, orientation="h") if horizontal else dict(x=categoria, y=valor)
    fig = px.bar(dados, **eixos, labels={valor: rotulo_valor, categoria: ""}, log_x=log and horizontal,
                 color_discrete_sequence=PALETA)
    rotulo_categoria = ROTULOS.get(categoria, categoria.replace("_", " ").capitalize())
    if horizontal:
        fig.update_yaxes(autorange="reversed")
        return _padronizar(fig, titulo, rotulo_valor, rotulo_categoria)
    return _padronizar(fig, titulo, rotulo_categoria, rotulo_valor)


def boxplot(mensal, grupo, titulo):
    """Distribuição da inadimplência mensal de cada grupo, ordenada pela mediana."""
    ordem = (mensal.groupby(grupo, observed=True)["taxa_inadimplencia"].median()
             .sort_values(ascending=False).index.astype(str).tolist())
    dados = mensal.assign(**{grupo: mensal[grupo].astype(str)})
    fig = px.box(dados, x=grupo, y="taxa_inadimplencia", category_orders={grupo: ordem}, color_discrete_sequence=PALETA,
                 labels={"taxa_inadimplencia": "Inadimplência mensal (%)", grupo: grupo.upper()})
    return _padronizar(fig, titulo, grupo.upper(), "Inadimplência mensal (%)")
