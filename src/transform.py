"""Etapa T do ETL (Transform) e carga (Load) em Parquet.

Decisões de tratamento (cada uma tem teste em tests/test_transform.py):
1. Valores monetários vêm como texto no padrão brasileiro ("1.234,56") e viram número.
2. numero_de_operacoes = -1 significa SUPRESSÃO POR SIGILO do BCB (combinações com
   poucas operações), não erro: entra como 0 na soma e é contado em coluna própria.
3. Espaços extras nas categorias são normalizados; categoria ausente vira "Não informado".
4. Linhas duplicadas exatas são removidas.
5. grupo_credito (Livre/Direcionado) vem do campo oficial "origem".
6. Minimização: faixas de vencimento, submodalidade e indexador são descartados.
7. Validação final: o total nacional precisa bater com o valor conferido no arquivo bruto.

Uso:  python -m src.transform
"""
import zipfile
from pathlib import Path
from typing import Iterator

import pandas as pd

from src import config

# Colunas do CSV bruto de que o projeto precisa. Se o BCB mudar o layout, o ETL avisa.
COLUNAS_BRUTAS_NECESSARIAS = ["data_base", *config.COLUNAS_CATEGORICAS, "numero_de_operacoes", *config.COLUNAS_MONETARIAS]


def converter_valor_br(serie: pd.Series) -> pd.Series:
    """Converte texto no padrão brasileiro ("1.234,56") em número (1234.56).

    Remove o separador de milhar (ponto) e troca a vírgula decimal por ponto.
    errors="raise": se aparecer um valor que não é número, o ETL para e avisa,
    em vez de virar NaN silenciosamente.
    """
    texto = serie.astype(str).str.strip().str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="raise")


def tratar_supressao(serie: pd.Series) -> pd.DataFrame:
    """Separa o número de operações da marcação de sigilo (-1).

    Retorna duas colunas:
    - numero_operacoes: valor válido para somar (o -1 vira 0);
    - operacao_suprimida: 1 quando a combinação foi suprimida pelo BCB, 0 caso contrário.
    """
    operacoes = pd.to_numeric(serie, errors="raise").astype("int64")
    if (operacoes < -1).any():
        raise ValueError("numero_de_operacoes tem valor negativo diferente de -1 (não previsto pela metodologia).")
    return pd.DataFrame(
        {
            "numero_operacoes": operacoes.where(operacoes >= 0, 0),
            "operacao_suprimida": (operacoes == -1).astype("int64"),
        },
        index=serie.index,
    )


def relatorio_qualidade(df_bruto: pd.DataFrame) -> dict:
    """Mede a qualidade do arquivo bruto de um mês, antes de qualquer limpeza."""
    return {
        "ano_mes": str(df_bruto["data_base"].iloc[0])[:7],
        "linhas": int(len(df_bruto)),
        "nulos": int(df_bruto.isna().sum().sum()),
        "duplicadas": int(df_bruto.duplicated().sum()),
        "combinacoes_suprimidas": int((df_bruto["numero_de_operacoes"].astype(str).str.strip() == "-1").sum()),
    }


def limpar_mes(df_bruto: pd.DataFrame) -> pd.DataFrame:
    """Aplica as regras de limpeza a um mês e devolve só as colunas usadas na análise."""
    faltando = [c for c in COLUNAS_BRUTAS_NECESSARIAS if c not in df_bruto.columns]
    if faltando:
        raise ValueError(f"Colunas obrigatórias ausentes no arquivo do BCB: {faltando}")

    df = df_bruto[COLUNAS_BRUTAS_NECESSARIAS].drop_duplicates().copy()

    for coluna in config.COLUNAS_CATEGORICAS:
        df[coluna] = (
            df[coluna].fillna("Não informado").astype(str)
            .str.strip().str.replace(r"\s+", " ", regex=True)
        )

    # data_base vem como "2025-12-31"; a análise é mensal, então guardamos "2025-12".
    df["ano_mes"] = df["data_base"].astype(str).str[:7]

    for coluna in config.COLUNAS_MONETARIAS:
        df[coluna] = converter_valor_br(df[coluna])

    supressao = tratar_supressao(df["numero_de_operacoes"])
    df["numero_operacoes"] = supressao["numero_operacoes"]
    df["operacao_suprimida"] = supressao["operacao_suprimida"]

    df["grupo_credito"] = df["origem"].map(config.GRUPO_POR_ORIGEM)
    desconhecidas = df.loc[df["grupo_credito"].isna(), "origem"].unique().tolist()
    if desconhecidas:
        raise ValueError(f"Valor de origem não previsto: {desconhecidas}")

    df["regiao"] = df["uf"].map(config.REGIAO_POR_UF).fillna("Não informado")

    colunas_finais = [
        "ano_mes", "uf", "regiao", "cliente", "segmento", "cnae_ocupacao", "porte",
        "modalidade", "grupo_credito", "numero_operacoes", "operacao_suprimida",
        *config.COLUNAS_MONETARIAS,
    ]
    return df[colunas_finais].reset_index(drop=True)


# Métricas somadas em todas as agregações.
METRICAS_SOMA = ["numero_operacoes", "operacao_suprimida", *config.COLUNAS_MONETARIAS]


def agregar(df: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    """Soma as métricas no nível pedido (ex.: mês × cliente).

    A coluna operacao_suprimida, somada, passa a significar "quantas combinações do
    arquivo original foram suprimidas", por isso é renomeada.
    """
    return (
        df.groupby(chaves, as_index=False, observed=True)[METRICAS_SOMA].sum()
        .rename(columns={"operacao_suprimida": "combinacoes_suprimidas"})
    )


def validar_total(resumo: pd.DataFrame, mes: str, esperado: float, tolerancia: float) -> float:
    """Confere a carteira ativa nacional de um mês contra o valor de referência."""
    total = float(resumo.loc[resumo["ano_mes"] == mes, "carteira_ativa"].sum())
    desvio = abs(total / esperado - 1)
    if desvio > tolerancia:
        raise ValueError(
            f"Carteira de {mes} = R$ {total / 1e12:.3f} tri diverge {desvio:.1%} "
            f"da referência R$ {esperado / 1e12:.3f} tri."
        )
    print(f"[transform] validação ok: carteira de {mes} = R$ {total / 1e12:.3f} tri (desvio {desvio:.2%})")
    return total


def ler_meses_do_zip(caminho: Path) -> Iterator[pd.DataFrame]:
    """Lê, um por vez, os CSVs mensais de um ZIP (cada um tem ~100 MB; ler um por vez poupa memória).

    sep=";" e encoding="utf-8-sig" seguem o formato do BCB (o "-sig" remove o BOM).
    dtype=str: tudo entra como texto e a conversão é feita de forma controlada em limpar_mes.
    O pandas respeita as aspas, então um ";" dentro do nome de um setor não quebra a coluna.
    """
    with zipfile.ZipFile(caminho) as arquivo_zip:
        nomes = sorted(n for n in arquivo_zip.namelist() if n.endswith(".csv"))
        for nome in nomes:
            with arquivo_zip.open(nome) as csv:
                yield pd.read_csv(csv, sep=";", encoding="utf-8-sig", dtype=str)


def _como_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Converte colunas de texto em 'category': o Parquet fica bem menor e mais rápido de ler.

    ano_mes continua texto, porque os filtros de período comparam meses com >= e <=
    (texto "2024-01" < "2025-12" funciona; categoria sem ordem não permite essa comparação).
    No pandas 3, texto tem o tipo "str" (e não mais "object"), por isso os dois são incluídos.
    """
    for coluna in df.select_dtypes(include=["object", "str"]).columns:
        if coluna != "ano_mes":
            df[coluna] = df[coluna].astype("category")
    return df


def executar(
    dir_raw: Path | None = None,
    dir_processed: Path | None = None,
    anos=None,
    meses_por_ano: int = 12,
    validar: bool = True,
) -> dict[str, pd.DataFrame]:
    """Roda a transformação completa e grava os Parquets em dir_processed."""
    dir_raw = Path(dir_raw or config.DIR_RAW)
    dir_processed = Path(dir_processed or config.DIR_PROCESSED)
    anos = anos or config.ANOS

    partes = {"fato_credito": [], "fato_setor": [], "resumo_mensal": []}
    qualidade = []

    for ano in anos:
        caminho = dir_raw / f"scrdata_{ano}.zip"
        if not caminho.exists():
            raise FileNotFoundError(f"{caminho} não encontrado. Rode antes: python -m src.extract")

        meses_lidos = 0
        for df_bruto in ler_meses_do_zip(caminho):
            qualidade.append(relatorio_qualidade(df_bruto))
            df = limpar_mes(df_bruto)
            partes["fato_credito"].append(agregar(df, config.CHAVES_FATO_CREDITO))
            partes["fato_setor"].append(agregar(df, config.CHAVES_FATO_SETOR))
            partes["resumo_mensal"].append(agregar(df, config.CHAVES_RESUMO))
            meses_lidos += 1
            print(f"[transform] {qualidade[-1]['ano_mes']}: {len(df_bruto):,} linhas brutas -> {len(partes['fato_credito'][-1]):,} no fato")

        if meses_lidos != meses_por_ano:
            raise ValueError(f"{caminho.name}: {meses_lidos} meses encontrados, esperados {meses_por_ano}.")

    tabelas = {nome: pd.concat(lista, ignore_index=True) for nome, lista in partes.items()}
    tabelas["qualidade_mensal"] = pd.DataFrame(qualidade)

    if validar:
        validar_total(tabelas["resumo_mensal"], config.MES_VALIDACAO, config.CARTEIRA_ESPERADA_VALIDACAO, config.TOLERANCIA_VALIDACAO)

    dir_processed.mkdir(parents=True, exist_ok=True)
    for nome, tabela in tabelas.items():
        destino = dir_processed / f"{nome}.parquet"
        _como_categoria(tabela).to_parquet(destino, index=False)
        print(f"[transform] {destino.name}: {tabela.shape[0]:,} linhas, {destino.stat().st_size / 1e6:.1f} MB")

    return tabelas


def main() -> None:
    executar()


if __name__ == "__main__":
    main()
