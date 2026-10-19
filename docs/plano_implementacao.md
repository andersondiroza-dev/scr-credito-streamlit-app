# Panorama do Crédito Nacional (Streamlit): Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** construir o pipeline ETL → EDA → app Streamlit sobre o SCR.data (BCB, 2024–2025)
que responde "onde o crédito cresce e se esse crescimento vem com mais risco", pronto
para o deploy no Streamlit Community Cloud.

**Architecture:**
- `src/extract.py` baixa os ZIPs oficiais.
- `src/transform.py` limpa e agrega os 24 CSVs mensais em Parquets versionados em
  `data/processed/`.
- `src/analysis.py` concentra indicadores e estatísticas, usados pelo notebook de EDA e
  pelo app.
- `app.py` (com `st.navigation`) apenas lê os Parquets. Os gráficos são montados em
  `src/graficos.py` e os componentes de tela em `src/interface.py`.

**Tech Stack:** Python 3.14 local / 3.12 no deploy, pandas, NumPy, SciPy, PyArrow, Plotly,
Streamlit, requests; pytest, Jupyter e Matplotlib só para desenvolvimento.

**Spec:** `docs/especificacao_projeto.md`

## Global Constraints

- Projeto em `~/Desktop/SCTEC/scr-credito-streamlit`. **Nenhum caminho absoluto no código**:
  todos os caminhos derivam de `src/config.py` (`RAIZ_PROJETO`).
- Período: 2024-01 a 2025-12. Fonte: `https://www.bcb.gov.br/pda/desig/scrdata_{ano}.zip`,
  licença ODbL.
- Todo texto visível (app, README, notebook, comentários, mensagens de commit) em
  português do Brasil, comentado de forma didática (o leitor é um avaliador do curso).
- Commits pequenos, no imperativo, em PT ("adiciona…", "cria…"). **Sem a linha
  `Co-Authored-By`.** O uso de IA é citado na seção Créditos do README.
- Branches: `main` (estável) ← `develop` ← `feature/etl`, `feature/eda`, `feature/app`,
  `docs/readme`, juntadas com `git merge --no-ff`.
- Nunca versionar `data/raw/`, `.venv/`, `.env`, nem arquivos maiores que 50 MB.
- Taxa de inadimplência = `carteira_inadimplencia / carteira_ativa × 100` (vencido > 90 dias).
- Validação: carteira ativa total de 2025-12 = 7,444 tri ± 1%.
- Gráficos: título, eixos com unidade, legenda e anotação "Fonte: Banco Central do Brasil,
  SCR.data".
- Não usar travessão (—) em textos visíveis; usar vírgula, dois-pontos ou parênteses.
- Todos os comandos rodam a partir da raiz do projeto, com o `.venv` ativado
  (`source .venv/bin/activate`).

---

### Task 1: Ambiente, esqueleto e configuração central

**Files:**
- Create: `.gitignore`, `.env.example`, `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`
- Create: `src/__init__.py`, `src/config.py`, `tests/__init__.py`, `tests/test_config.py`
- Create: `data/raw/.gitkeep`, `data/processed/.gitkeep`, `outputs/.gitkeep`, `notebooks/.gitkeep`

**Interfaces:**
- Produces: `src.config` com `RAIZ_PROJETO`, `DIR_RAW`, `DIR_PROCESSED`, `DIR_OUTPUTS`,
  `ANOS`, `URL_ZIP`, `URL_DATASET`, `COLUNAS_MONETARIAS`, `COLUNAS_CATEGORICAS`,
  `CHAVES_FATO_CREDITO`, `CHAVES_FATO_SETOR`, `CHAVES_RESUMO`, `GRUPO_POR_ORIGEM`,
  `REGIAO_POR_UF`, `MES_VALIDACAO`, `CARTEIRA_ESPERADA_VALIDACAO`, `TOLERANCIA_VALIDACAO`

- [ ] **Step 1: Criar a branch develop e o ambiente virtual**

```bash
git checkout -b develop
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install streamlit pandas numpy scipy pyarrow plotly requests
pip install pytest jupyter nbconvert ipykernel matplotlib
```

- [ ] **Step 2: Fixar as versões instaladas**

```bash
pip freeze | grep -iE '^(streamlit|pandas|numpy|scipy|pyarrow|plotly|requests)==' > requirements.txt
{ echo "-r requirements.txt"; pip freeze | grep -iE '^(pytest|jupyter|nbconvert|ipykernel|matplotlib)=='; } > requirements-dev.txt
cat requirements.txt requirements-dev.txt
```

Expected: 7 linhas em `requirements.txt` e 6 em `requirements-dev.txt`, todas com `==`.

Verificar se as versões fixadas existem para o Python 3.12 (é o que o deploy usa):
`numpy>=2.4` e `scipy>=1.17` exigem Python ≥ 3.11, o que está ok. Se alguma versão
publicar wheel só para 3.13+, rebaixar essa biblioteca para a última versão compatível
com 3.12.

- [ ] **Step 3: Criar `.gitignore`, `.env.example` e `pyproject.toml`**

`.gitignore`:
```gitignore
# Ambiente virtual e caches do Python
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ipynb_checkpoints/

# Dados brutos do BCB (~2,4 GB): são baixados por src/extract.py, não versionados
data/raw/*
!data/raw/.gitkeep
*.zip.part

# Segredos e configurações locais (o projeto não usa credenciais, mas fica a proteção)
.env
.streamlit/secrets.toml

# Sistema operacional
.DS_Store
```

`.env.example`:
```bash
# Variáveis opcionais. Copie para .env apenas se quiser mudar os caminhos padrão.
# O projeto NÃO usa senhas nem chaves de API (os dados do BCB são públicos).
SCR_DIR_RAW=
SCR_DIR_PROCESSED=
```

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 4: Escrever o teste da configuração**

`tests/__init__.py`: arquivo vazio.

`tests/test_config.py`:
```python
"""Garante que a configuração não depende de caminhos absolutos da máquina do autor."""
from src import config


def test_diretorios_derivam_da_raiz_do_projeto():
    assert config.DIR_RAW == config.RAIZ_PROJETO / "data" / "raw"
    assert config.DIR_PROCESSED == config.RAIZ_PROJETO / "data" / "processed"


def test_url_oficial_do_bcb():
    assert config.URL_ZIP.format(ano=2024) == "https://www.bcb.gov.br/pda/desig/scrdata_2024.zip"


def test_todas_as_27_ufs_tem_regiao():
    assert len(config.REGIAO_POR_UF) == 27
    assert set(config.REGIAO_POR_UF.values()) == {"Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"}


def test_origem_cobre_livre_e_direcionado():
    assert set(config.GRUPO_POR_ORIGEM.values()) == {"Livre", "Direcionado"}
```

- [ ] **Step 5: Rodar e ver falhar**

Run: `pytest tests/test_config.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src'` (ou falta de `config`)

- [ ] **Step 6: Implementar `src/config.py`**

`src/__init__.py`: arquivo vazio.

`src/config.py`:
```python
"""Configurações centrais do projeto.

Tudo o que pode mudar (caminhos, período, URLs, nomes de colunas) fica aqui, em um
único lugar. Os demais módulos importam daqui e nunca usam caminhos absolutos: tudo é
calculado a partir da pasta raiz do projeto, para o código rodar em qualquer máquina.
"""
import os
from pathlib import Path

# Pasta raiz do projeto (a que contém app.py). __file__ é src/config.py, então subimos 2 níveis.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent

# As variáveis de ambiente são opcionais (ver .env.example). Sem elas, valem os padrões abaixo.
DIR_RAW = Path(os.getenv("SCR_DIR_RAW") or RAIZ_PROJETO / "data" / "raw")
DIR_PROCESSED = Path(os.getenv("SCR_DIR_PROCESSED") or RAIZ_PROJETO / "data" / "processed")
DIR_OUTPUTS = RAIZ_PROJETO / "outputs"

# Recorte temporal da análise: 24 meses (jan/2024 a dez/2025).
ANOS = (2024, 2025)

# Fonte oficial: arquivos anuais do SCR.data publicados pelo Banco Central (licença ODbL).
URL_ZIP = "https://www.bcb.gov.br/pda/desig/scrdata_{ano}.zip"
URL_DATASET = "https://dadosabertos.bcb.gov.br/dataset/scr_data"

# Colunas monetárias mantidas (em R$). As faixas de vencimento foram descartadas
# por não responderem à pergunta do projeto (princípio de minimização de dados).
COLUNAS_MONETARIAS = [
    "carteira_a_vencer",
    "vencido_de_15_ate_90_dias",
    "carteira_vencida",
    "carteira_ativa",
    "carteira_inadimplencia",  # parcela vencida há mais de 90 dias
    "ativo_problematico",
]

# Colunas de texto (dimensões) que passam por limpeza de espaços.
COLUNAS_CATEGORICAS = ["uf", "segmento", "cliente", "cnae_ocupacao", "porte", "modalidade", "origem"]

# Níveis de agregação de cada tabela de saída.
CHAVES_FATO_CREDITO = ["ano_mes", "uf", "regiao", "cliente", "segmento", "modalidade", "grupo_credito", "porte"]
CHAVES_FATO_SETOR = ["ano_mes", "cliente", "cnae_ocupacao"]
CHAVES_RESUMO = ["ano_mes", "cliente"]

# Classificação oficial do BCB: recursos "com destinação específica" são crédito direcionado
# (ex.: rural, imobiliário com recursos da poupança); "sem destinação" é crédito livre.
GRUPO_POR_ORIGEM = {
    "Sem destinação específica": "Livre",
    "Com destinação específica": "Direcionado",
}

REGIAO_POR_UF = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste",
    "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

# Validação do ETL: total da carteira ativa nacional em dez/2025, conferido no arquivo
# bruto do BCB em 19/10/2026. Se o resultado divergir mais de 1%, algo deu errado.
MES_VALIDACAO = "2025-12"
CARTEIRA_ESPERADA_VALIDACAO = 7.444e12
TOLERANCIA_VALIDACAO = 0.01
```

- [ ] **Step 7: Rodar e ver passar**

Run: `pytest tests/test_config.py -v`
Expected: 4 passed

- [ ] **Step 8: Criar as pastas vazias versionadas e fazer o commit**

```bash
mkdir -p data/raw data/processed outputs notebooks
touch data/raw/.gitkeep data/processed/.gitkeep outputs/.gitkeep notebooks/.gitkeep
git add .gitignore .env.example pyproject.toml requirements.txt requirements-dev.txt src tests data outputs notebooks
git commit -m "cria estrutura do projeto e configuração central"
```

---

### Task 2: Extração (download dos ZIPs oficiais)

**Files:**
- Create: `src/extract.py`
- Test: `tests/test_extract.py`

**Interfaces:**
- Consumes: `config.URL_ZIP`, `config.DIR_RAW`, `config.ANOS`
- Produces: `url_do_ano(ano: int) -> str`; `baixar_zip(ano: int, destino: Path | None = None, tentativas: int = 3, espera_s: float = 5.0) -> Path`; `main() -> None`

- [ ] **Step 1: Criar a branch da etapa**

```bash
git checkout develop && git checkout -b feature/etl
```

- [ ] **Step 2: Escrever os testes (sem internet: o `requests.get` é simulado)**

`tests/test_extract.py`:
```python
"""Testes da extração. Nenhum teste acessa a internet: o download é simulado."""
import io
import zipfile

import pytest
import requests

from src import extract


def _zip_em_memoria() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("scrdata_209901.csv", "data_base;uf\n")
    return buffer.getvalue()


class RespostaFalsa:
    """Imita o objeto de resposta do requests usado com stream=True."""

    def __init__(self, conteudo: bytes):
        self.conteudo = conteudo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield self.conteudo


def test_url_do_ano():
    assert extract.url_do_ano(2025) == "https://www.bcb.gov.br/pda/desig/scrdata_2025.zip"


def test_nao_baixa_de_novo_se_arquivo_existe(tmp_path, monkeypatch):
    (tmp_path / "scrdata_2024.zip").write_bytes(_zip_em_memoria())

    def nao_deveria_chamar(*args, **kwargs):
        raise AssertionError("não deveria baixar")

    monkeypatch.setattr(extract.requests, "get", nao_deveria_chamar)
    caminho = extract.baixar_zip(2024, destino=tmp_path)
    assert caminho.name == "scrdata_2024.zip"


def test_baixa_e_valida_zip(tmp_path, monkeypatch):
    monkeypatch.setattr(extract.requests, "get", lambda *a, **k: RespostaFalsa(_zip_em_memoria()))
    caminho = extract.baixar_zip(2099, destino=tmp_path)
    assert zipfile.is_zipfile(caminho)
    assert not (tmp_path / "scrdata_2099.zip.part").exists()


def test_arquivo_que_nao_e_zip_e_rejeitado(tmp_path, monkeypatch):
    monkeypatch.setattr(extract.requests, "get", lambda *a, **k: RespostaFalsa(b"<html>erro</html>"))
    with pytest.raises(ValueError, match="não é um ZIP válido"):
        extract.baixar_zip(2099, destino=tmp_path, tentativas=1)
    assert not (tmp_path / "scrdata_2099.zip").exists()


def test_falha_de_rede_tenta_de_novo_e_desiste(tmp_path, monkeypatch):
    chamadas = []

    def sempre_falha(*args, **kwargs):
        chamadas.append(1)
        raise requests.ConnectionError("sem rede")

    monkeypatch.setattr(extract.requests, "get", sempre_falha)
    with pytest.raises(requests.ConnectionError):
        extract.baixar_zip(2099, destino=tmp_path, tentativas=3, espera_s=0)
    assert len(chamadas) == 3
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `pytest tests/test_extract.py -v`
Expected: FAIL com `ImportError: cannot import name 'extract'`

- [ ] **Step 4: Implementar `src/extract.py`**

```python
"""Etapa E do ETL (Extract): download dos arquivos públicos do SCR.data.

O portal de dados abertos do BCB não oferece API para consultar o SCR.data com filtros:
os dados são publicados como um arquivo ZIP por ano, com um CSV por mês. Por isso a
extração baixa os ZIPs inteiros, uma única vez, para data/raw/ (pasta fora do Git).

Uso:  python -m src.extract
Alternativa manual: baixar os ZIPs pelo navegador e salvá-los em data/raw/.
"""
import time
import zipfile
from pathlib import Path

import requests

from src import config


def url_do_ano(ano: int) -> str:
    """Monta a URL oficial do ZIP de um ano."""
    return config.URL_ZIP.format(ano=ano)


def baixar_zip(ano: int, destino: Path | None = None, tentativas: int = 3, espera_s: float = 5.0) -> Path:
    """Baixa o ZIP de um ano e devolve o caminho do arquivo salvo.

    - Se o arquivo já existir, não baixa de novo (economiza ~1,2 GB por ano).
    - Baixa primeiro para um arquivo ".part" e só renomeia no fim: assim um download
      interrompido nunca fica parecendo um arquivo completo.
    - Em falha de rede, tenta novamente até `tentativas` vezes.
    - Confere se o conteúdo é mesmo um ZIP (o servidor pode devolver uma página de erro).
    """
    destino = Path(destino or config.DIR_RAW)
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / f"scrdata_{ano}.zip"

    if arquivo.exists() and arquivo.stat().st_size > 0:
        print(f"[extract] {arquivo.name} já existe; download ignorado.")
        return arquivo

    temporario = destino / f"scrdata_{ano}.zip.part"
    for tentativa in range(1, tentativas + 1):
        try:
            print(f"[extract] baixando {url_do_ano(ano)} (tentativa {tentativa}/{tentativas})...")
            with requests.get(url_do_ano(ano), stream=True, timeout=60) as resposta:
                resposta.raise_for_status()
                with open(temporario, "wb") as saida:
                    for bloco in resposta.iter_content(chunk_size=1024 * 1024):
                        saida.write(bloco)
            break
        except requests.RequestException as erro:
            print(f"[extract] falha: {erro}")
            temporario.unlink(missing_ok=True)
            if tentativa == tentativas:
                raise
            time.sleep(espera_s)

    if not zipfile.is_zipfile(temporario):
        temporario.unlink(missing_ok=True)
        raise ValueError(f"O arquivo baixado para {ano} não é um ZIP válido.")

    temporario.rename(arquivo)
    print(f"[extract] salvo em {arquivo} ({arquivo.stat().st_size / 1e6:.0f} MB)")
    return arquivo


def main() -> None:
    for ano in config.ANOS:
        baixar_zip(ano)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Rodar e ver passar**

Run: `pytest tests/test_extract.py -v`
Expected: 5 passed

- [ ] **Step 6: Colocar os ZIPs reais em `data/raw/`**

Os ZIPs de 2024 e 2025 já existem em `~/Downloads` (baixados em set/2026). Primeiro tente
o download oficial, que é o caminho reproduzível:
```bash
python -m src.extract
```
Se a rede bloquear o bcb.gov.br, copie os arquivos que já estão em `~/Downloads` (o
script reconhece que eles existem e pula o download):
```bash
cp ~/Downloads/scrdata_2024.zip ~/Downloads/scrdata_2025.zip data/raw/ && python -m src.extract
```
Expected: duas linhas `[extract] ... salvo em` ou `já existe; download ignorado.`; `git status` não mostra os ZIPs.

- [ ] **Step 7: Commit**

```bash
git add src/extract.py tests/test_extract.py
git commit -m "adiciona extração dos arquivos do SCR.data com nova tentativa e validação"
```

---

### Task 3: Transformação, parte 1: limpeza de cada mês

**Files:**
- Create: `src/transform.py`
- Test: `tests/test_transform.py`

**Interfaces:**
- Consumes: `config.COLUNAS_MONETARIAS`, `config.COLUNAS_CATEGORICAS`, `config.GRUPO_POR_ORIGEM`, `config.REGIAO_POR_UF`
- Produces: `converter_valor_br(serie: pd.Series) -> pd.Series`; `tratar_supressao(serie: pd.Series) -> pd.DataFrame` (colunas `numero_operacoes`, `operacao_suprimida`); `relatorio_qualidade(df_bruto: pd.DataFrame) -> dict` (chaves `ano_mes`, `linhas`, `nulos`, `duplicadas`, `combinacoes_suprimidas`); `limpar_mes(df_bruto: pd.DataFrame) -> pd.DataFrame`; constante `COLUNAS_BRUTAS_NECESSARIAS`

- [ ] **Step 1: Escrever os testes**

`tests/test_transform.py`:
```python
"""Testes das regras de limpeza (transform). Cada regra documentada no README tem um teste."""
import pandas as pd
import pytest

from src import transform


def linha_bruta(**alteracoes) -> dict:
    """Uma linha no formato exato do CSV do BCB (tudo texto, números no padrão brasileiro)."""
    base = {
        "data_base": "2025-12-31", "uf": "SC", "segmento": "Banco", "cliente": "PF",
        "cnae_ocupacao": "Assalariado", "porte": "Até 1 salário mínimo",
        "modalidade": "Empréstimos", "submodalidade": "Crédito pessoal",
        "origem": "Sem destinação específica", "indexador": "Prefixado",
        "numero_de_operacoes": "10",
        "carteira_a_vencer": "900,00", "vencido_de_15_ate_90_dias": "40,00",
        "carteira_vencida": "100,00", "carteira_ativa": "1.000,00",
        "carteira_inadimplencia": "60,00", "ativo_problematico": "80,00",
    }
    base.update(alteracoes)
    return base


def test_converter_valor_br():
    serie = pd.Series(["1.234,56", "0,00", "-12,50", " 7,10 "])
    assert transform.converter_valor_br(serie).tolist() == [1234.56, 0.0, -12.5, 7.1]


def test_converter_valor_br_rejeita_texto_invalido():
    with pytest.raises(ValueError):
        transform.converter_valor_br(pd.Series(["abc"]))


def test_supressao_vira_zero_e_e_contada():
    resultado = transform.tratar_supressao(pd.Series(["5", "-1", "0"]))
    assert resultado["numero_operacoes"].tolist() == [5, 0, 0]
    assert resultado["operacao_suprimida"].tolist() == [0, 1, 0]


def test_supressao_rejeita_negativo_diferente_de_menos_um():
    with pytest.raises(ValueError):
        transform.tratar_supressao(pd.Series(["-2"]))


def test_limpar_mes_converte_tipos_e_cria_colunas():
    df = pd.DataFrame([linha_bruta(modalidade="Financiamentos  rurais ", origem="Com destinação específica")])
    limpo = transform.limpar_mes(df)
    linha = limpo.iloc[0]
    assert linha["ano_mes"] == "2025-12"
    assert linha["modalidade"] == "Financiamentos rurais"  # espaços normalizados
    assert linha["grupo_credito"] == "Direcionado"
    assert linha["regiao"] == "Sul"
    assert linha["carteira_ativa"] == 1000.0
    assert "indexador" not in limpo.columns  # coluna descartada por minimização


def test_limpar_mes_remove_duplicadas_exatas():
    df = pd.DataFrame([linha_bruta(), linha_bruta()])
    assert len(transform.limpar_mes(df)) == 1


def test_limpar_mes_preenche_categoria_ausente():
    df = pd.DataFrame([linha_bruta(porte=None)])
    assert transform.limpar_mes(df).iloc[0]["porte"] == "Não informado"


def test_limpar_mes_falha_com_origem_desconhecida():
    df = pd.DataFrame([linha_bruta(origem="Outra coisa")])
    with pytest.raises(ValueError, match="origem"):
        transform.limpar_mes(df)


def test_limpar_mes_falha_sem_coluna_obrigatoria():
    df = pd.DataFrame([linha_bruta()]).drop(columns=["carteira_ativa"])
    with pytest.raises(ValueError, match="carteira_ativa"):
        transform.limpar_mes(df)


def test_relatorio_qualidade():
    df = pd.DataFrame([linha_bruta(), linha_bruta(), linha_bruta(numero_de_operacoes="-1", porte=None)])
    rel = transform.relatorio_qualidade(df)
    assert rel == {"ano_mes": "2025-12", "linhas": 3, "nulos": 1, "duplicadas": 1, "combinacoes_suprimidas": 1}
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_transform.py -v`
Expected: FAIL com `ImportError: cannot import name 'transform'`

- [ ] **Step 3: Implementar a primeira parte de `src/transform.py`**

```python
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest tests/test_transform.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add src/transform.py tests/test_transform.py
git commit -m "adiciona regras de limpeza dos arquivos mensais do SCR.data"
```

---

### Task 4: Transformação, parte 2: agregação, validação e carga em Parquet

**Files:**
- Modify: `src/transform.py` (acrescentar no fim do arquivo)
- Modify: `tests/test_transform.py` (acrescentar no fim do arquivo)
- Create: `data/processed/fato_credito.parquet`, `fato_setor.parquet`, `resumo_mensal.parquet`, `qualidade_mensal.parquet` (gerados)

**Interfaces:**
- Consumes: `limpar_mes`, `relatorio_qualidade` (Task 3); `config.CHAVES_*`, `config.MES_VALIDACAO`, `config.CARTEIRA_ESPERADA_VALIDACAO`, `config.TOLERANCIA_VALIDACAO`
- Produces: `METRICAS_SOMA: list[str]`; `agregar(df: pd.DataFrame, chaves: list[str]) -> pd.DataFrame` (renomeia `operacao_suprimida` para `combinacoes_suprimidas`); `validar_total(resumo: pd.DataFrame, mes: str, esperado: float, tolerancia: float) -> float`; `ler_meses_do_zip(caminho: Path) -> Iterator[pd.DataFrame]`; `executar(dir_raw: Path | None = None, dir_processed: Path | None = None, anos=None, meses_por_ano: int = 12, validar: bool = True) -> dict[str, pd.DataFrame]` (chaves `fato_credito`, `fato_setor`, `resumo_mensal`, `qualidade_mensal`)
- Parquet `fato_credito`: colunas `ano_mes, uf, regiao, cliente, segmento, modalidade, grupo_credito, porte, numero_operacoes, combinacoes_suprimidas, carteira_a_vencer, vencido_de_15_ate_90_dias, carteira_vencida, carteira_ativa, carteira_inadimplencia, ativo_problematico`

- [ ] **Step 1: Escrever os testes (acrescentar ao fim de `tests/test_transform.py`)**

```python
import zipfile as _zipfile


def _csv_bcb(linhas: list[dict]) -> str:
    """Gera um CSV idêntico ao do BCB: separador ';', todos os campos entre aspas, BOM."""
    colunas = list(linhas[0].keys())
    corpo = [";".join(f'"{l[c]}"' for c in colunas) for l in linhas]
    return "﻿" + ";".join(colunas) + "\n" + "\n".join(corpo) + "\n"


def test_agregar_soma_metricas_e_renomeia_supressao():
    df = transform.limpar_mes(pd.DataFrame([
        linha_bruta(cnae_ocupacao="Assalariado"),
        linha_bruta(cnae_ocupacao="Autônomo", numero_de_operacoes="-1"),
    ]))
    agregado = transform.agregar(df, ["ano_mes", "cliente"])
    assert len(agregado) == 1
    assert agregado.iloc[0]["carteira_ativa"] == 2000.0
    assert agregado.iloc[0]["numero_operacoes"] == 10
    assert agregado.iloc[0]["combinacoes_suprimidas"] == 1


def test_validar_total_aceita_dentro_da_tolerancia():
    resumo = pd.DataFrame({"ano_mes": ["2025-12", "2025-12"], "carteira_ativa": [500.0, 505.0]})
    assert transform.validar_total(resumo, "2025-12", esperado=1000.0, tolerancia=0.01) == 1005.0


def test_validar_total_rejeita_divergencia():
    resumo = pd.DataFrame({"ano_mes": ["2025-12"], "carteira_ativa": [900.0]})
    with pytest.raises(ValueError, match="diverge"):
        transform.validar_total(resumo, "2025-12", esperado=1000.0, tolerancia=0.01)


def test_executar_ponta_a_ponta_com_zip_sintetico(tmp_path):
    raw, processed = tmp_path / "raw", tmp_path / "processed"
    raw.mkdir()
    with _zipfile.ZipFile(raw / "scrdata_2099.zip", "w") as z:
        z.writestr("scrdata_209901.csv", _csv_bcb([linha_bruta(data_base="2099-01-31", cnae_ocupacao="Comércio; reparação")]))
        z.writestr("scrdata_209902.csv", _csv_bcb([linha_bruta(data_base="2099-02-28")]))

    tabelas = transform.executar(dir_raw=raw, dir_processed=processed, anos=(2099,), meses_por_ano=2, validar=False)

    assert tabelas["resumo_mensal"]["ano_mes"].tolist() == ["2099-01", "2099-02"]
    assert set(tabelas["fato_setor"]["cnae_ocupacao"]) == {"Comércio; reparação", "Assalariado"}
    assert len(tabelas["qualidade_mensal"]) == 2
    for nome in ["fato_credito", "fato_setor", "resumo_mensal", "qualidade_mensal"]:
        assert (processed / f"{nome}.parquet").exists()


def test_executar_falha_se_faltar_mes(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    with _zipfile.ZipFile(raw / "scrdata_2099.zip", "w") as z:
        z.writestr("scrdata_209901.csv", _csv_bcb([linha_bruta(data_base="2099-01-31")]))
    with pytest.raises(ValueError, match="esperados 12"):
        transform.executar(dir_raw=raw, dir_processed=tmp_path / "p", anos=(2099,), validar=False)


def test_executar_falha_se_zip_ausente(tmp_path):
    with pytest.raises(FileNotFoundError, match="src.extract"):
        transform.executar(dir_raw=tmp_path, dir_processed=tmp_path / "p", anos=(2099,), validar=False)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_transform.py -v`
Expected: os 10 testes antigos passam e os 6 novos falham com `AttributeError: module 'src.transform' has no attribute 'agregar'` (ou similar)

- [ ] **Step 3: Implementar (acrescentar ao fim de `src/transform.py`)**

```python
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
    """
    for coluna in df.select_dtypes(include="object").columns:
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest -v`
Expected: todos os testes passam (4 config + 5 extract + 16 transform = 25 passed)

- [ ] **Step 5: Rodar o ETL real**

Run: `python -m src.transform`
Expected:
- 24 linhas `[transform] AAAA-MM: ...`
- `validação ok: carteira de 2025-12 = R$ 7.444 tri`
- 4 Parquets gravados

Depois confira o tamanho: `ls -lh data/processed/`. Cada arquivo precisa ter menos de 50 MB.
Se `fato_credito.parquet` passar disso, troque a compressão em `executar` para
`to_parquet(destino, index=False, compression="zstd")` e rode de novo.

- [ ] **Step 6: Commit dos Parquets e merge da etapa**

```bash
git add src/transform.py tests/test_transform.py data/processed/*.parquet
git commit -m "adiciona agregação, validação do total nacional e carga em Parquet"
git checkout develop && git merge --no-ff feature/etl -m "integra etapa de ETL"
```

---

### Task 5: Análise, parte 1: filtros e indicadores

**Files:**
- Create: `src/analysis.py`
- Test: `tests/test_analysis.py`, `tests/conftest.py`

**Interfaces:**
- Consumes: colunas do Parquet `fato_credito` (Task 4)
- Produces: `taxa_percentual(numerador, denominador)` (escalar → float; Series → Series; NaN quando o denominador é 0); `filtrar(fato, inicio: str, fim: str, clientes=None, segmentos=None, regioes=None, ufs=None, modalidades=None) -> pd.DataFrame`; `mes_base_comparacao(meses: list[str], inicio: str, fim: str) -> str`; `serie_mensal(fato, por: str | None = None) -> pd.DataFrame` (colunas `ano_mes`, [por], `carteira_ativa`, `carteira_inadimplencia`, `ativo_problematico`, `numero_operacoes`, `taxa_inadimplencia`, `taxa_ativo_problematico`); `kpis(fato, mes_base: str, mes_ref: str) -> dict` (chaves `carteira_base`, `carteira_ref`, `crescimento_pct`, `inadimplencia_base_pct`, `inadimplencia_ref_pct`, `participacao_fintech_pct`)
- Fixture pytest `fato_exemplo` em `tests/conftest.py`

- [ ] **Step 1: Criar a branch e o fixture compartilhado**

```bash
git checkout develop && git checkout -b feature/eda
```

`tests/conftest.py`:
```python
"""Dados sintéticos pequenos, com contas fáceis de conferir à mão."""
import pandas as pd
import pytest


@pytest.fixture
def fato_exemplo() -> pd.DataFrame:
    """Dois meses (2024-12 e 2025-12), dois segmentos, PF e PJ, duas UFs.

    Banco/PF/SC:     carteira 1000 -> 1100 (+10%), inadimplência 50 -> 66 (5% -> 6%)
    Fintech/PF/SP:   carteira  100 ->  200 (+100%), inadimplência 10 -> 30 (10% -> 15%)
    Banco/PJ/SP:     carteira  900 ->  900 (0%),   inadimplência 18 -> 18 (2% -> 2%)
    """
    linhas = [
        ("2024-12", "SC", "Sul", "PF", "Banco", "Empréstimos", "Livre", 1000.0, 50.0, 70.0),
        ("2024-12", "SP", "Sudeste", "PF", "Fintech", "Empréstimos", "Livre", 100.0, 10.0, 12.0),
        ("2024-12", "SP", "Sudeste", "PJ", "Banco", "Financiamentos", "Direcionado", 900.0, 18.0, 30.0),
        ("2025-12", "SC", "Sul", "PF", "Banco", "Empréstimos", "Livre", 1100.0, 66.0, 90.0),
        ("2025-12", "SP", "Sudeste", "PF", "Fintech", "Empréstimos", "Livre", 200.0, 30.0, 35.0),
        ("2025-12", "SP", "Sudeste", "PJ", "Banco", "Financiamentos", "Direcionado", 900.0, 18.0, 30.0),
    ]
    colunas = ["ano_mes", "uf", "regiao", "cliente", "segmento", "modalidade", "grupo_credito",
               "carteira_ativa", "carteira_inadimplencia", "ativo_problematico"]
    df = pd.DataFrame(linhas, columns=colunas)
    df["porte"] = "Total"
    df["numero_operacoes"] = 1
    df["combinacoes_suprimidas"] = 0
    return df
```

- [ ] **Step 2: Escrever os testes**

`tests/test_analysis.py`:
```python
"""Testes dos indicadores. Os valores esperados foram calculados à mão (ver conftest.py)."""
import math

import pandas as pd
import pytest

from src import analysis


def test_taxa_percentual_escalar_e_divisao_por_zero():
    assert analysis.taxa_percentual(5, 100) == 5.0
    assert math.isnan(analysis.taxa_percentual(5, 0))


def test_taxa_percentual_series():
    resultado = analysis.taxa_percentual(pd.Series([1.0, 2.0]), pd.Series([10.0, 0.0]))
    assert resultado.iloc[0] == 10.0
    assert math.isnan(resultado.iloc[1])


def test_filtrar_por_periodo_e_listas(fato_exemplo):
    f = analysis.filtrar(fato_exemplo, "2025-12", "2025-12", clientes=["PF"], segmentos=["Fintech"])
    assert len(f) == 1 and f.iloc[0]["carteira_ativa"] == 200.0


def test_filtrar_lista_vazia_nao_filtra(fato_exemplo):
    assert len(analysis.filtrar(fato_exemplo, "2024-12", "2025-12", clientes=[])) == 6


def test_mes_base_comparacao_usa_12_meses_antes_quando_disponivel():
    meses = ["2024-01", "2024-12", "2025-12"]
    assert analysis.mes_base_comparacao(meses, "2024-01", "2025-12") == "2024-12"


def test_mes_base_comparacao_cai_para_inicio_do_periodo():
    meses = ["2025-01", "2025-06"]
    assert analysis.mes_base_comparacao(meses, "2025-01", "2025-06") == "2025-01"


def test_serie_mensal_total(fato_exemplo):
    serie = analysis.serie_mensal(fato_exemplo)
    dez25 = serie.set_index("ano_mes").loc["2025-12"]
    assert dez25["carteira_ativa"] == 2200.0
    assert dez25["taxa_inadimplencia"] == pytest.approx(114 / 2200 * 100)


def test_serie_mensal_por_grupo(fato_exemplo):
    serie = analysis.serie_mensal(fato_exemplo, por="cliente")
    assert set(serie.columns) >= {"ano_mes", "cliente", "taxa_inadimplencia"}
    assert len(serie) == 4


def test_kpis(fato_exemplo):
    k = analysis.kpis(fato_exemplo, "2024-12", "2025-12")
    assert k["carteira_base"] == 2000.0
    assert k["carteira_ref"] == 2200.0
    assert k["crescimento_pct"] == pytest.approx(10.0)
    assert k["inadimplencia_ref_pct"] == pytest.approx(114 / 2200 * 100)
    assert k["participacao_fintech_pct"] == pytest.approx(200 / 2200 * 100)


def test_kpis_sem_dados_nao_quebra(fato_exemplo):
    k = analysis.kpis(fato_exemplo.iloc[0:0], "2024-12", "2025-12")
    assert k["carteira_ref"] == 0.0
    assert math.isnan(k["crescimento_pct"])
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `pytest tests/test_analysis.py -v`
Expected: FAIL com `ImportError: cannot import name 'analysis'`

- [ ] **Step 4: Implementar `src/analysis.py` (parte 1)**

```python
"""Indicadores e estatísticas do projeto.

Este módulo é a "fonte única da verdade" dos números: o notebook de EDA e o app
Streamlit chamam as mesmas funções, então um número nunca difere entre os dois.
"""
import numpy as np
import pandas as pd
from scipy import stats

METRICAS = ["carteira_ativa", "carteira_inadimplencia", "ativo_problematico", "numero_operacoes"]


def taxa_percentual(numerador, denominador):
    """numerador / denominador × 100, devolvendo NaN (e não erro) quando o denominador é 0."""
    if np.isscalar(denominador):
        return float("nan") if denominador == 0 else float(numerador) / float(denominador) * 100
    return numerador / denominador.replace(0, np.nan) * 100


def filtrar(fato, inicio, fim, clientes=None, segmentos=None, regioes=None, ufs=None, modalidades=None):
    """Aplica os filtros da barra lateral. Lista vazia ou None significa "todos"."""
    mascara = (fato["ano_mes"] >= inicio) & (fato["ano_mes"] <= fim)
    for coluna, valores in [("cliente", clientes), ("segmento", segmentos), ("regiao", regioes), ("uf", ufs), ("modalidade", modalidades)]:
        if valores:
            mascara &= fato[coluna].isin(valores)
    return fato[mascara]


def mes_base_comparacao(meses, inicio, fim):
    """Mês de comparação para o crescimento: 12 meses antes do fim, se estiver no período.

    Comparar sempre o mesmo mês (dez contra dez) evita confundir crescimento com
    sazonalidade. Se o período escolhido for menor que 12 meses, usa o início do período.
    """
    candidato = f"{int(fim[:4]) - 1}-{fim[5:7]}"
    return candidato if candidato >= inicio and candidato in meses else inicio


def serie_mensal(fato, por=None):
    """Soma as métricas por mês (e por grupo, se `por` for informado) e calcula as taxas."""
    chaves = ["ano_mes"] + ([por] if por else [])
    serie = fato.groupby(chaves, as_index=False, observed=True)[METRICAS].sum()
    serie["taxa_inadimplencia"] = taxa_percentual(serie["carteira_inadimplencia"], serie["carteira_ativa"])
    serie["taxa_ativo_problematico"] = taxa_percentual(serie["ativo_problematico"], serie["carteira_ativa"])
    return serie.sort_values(chaves).reset_index(drop=True)


def kpis(fato, mes_base, mes_ref):
    """Os 4 números principais da página Início."""
    base = fato[fato["ano_mes"] == mes_base]
    ref = fato[fato["ano_mes"] == mes_ref]
    carteira_base = float(base["carteira_ativa"].sum())
    carteira_ref = float(ref["carteira_ativa"].sum())
    return {
        "carteira_base": carteira_base,
        "carteira_ref": carteira_ref,
        "crescimento_pct": taxa_percentual(carteira_ref - carteira_base, carteira_base),
        "inadimplencia_base_pct": taxa_percentual(base["carteira_inadimplencia"].sum(), carteira_base),
        "inadimplencia_ref_pct": taxa_percentual(ref["carteira_inadimplencia"].sum(), carteira_ref),
        "participacao_fintech_pct": taxa_percentual(ref.loc[ref["segmento"] == "Fintech", "carteira_ativa"].sum(), carteira_ref),
    }
```

- [ ] **Step 5: Rodar e ver passar**

Run: `pytest tests/test_analysis.py -v`
Expected: 10 passed

- [ ] **Step 6: Commit**

```bash
git add src/analysis.py tests/test_analysis.py tests/conftest.py
git commit -m "adiciona filtros e indicadores de carteira e inadimplência"
```

---

### Task 6: Análise, parte 2: estatísticas (Spearman, tendência, HHI, descritivas)

**Files:**
- Modify: `src/analysis.py` (acrescentar no fim)
- Modify: `tests/test_analysis.py` (acrescentar no fim)

**Interfaces:**
- Consumes: `taxa_percentual`, `serie_mensal` (Task 5)
- Produces:
  - `crescimento_x_risco(fato, mes_base, mes_ref, chaves=("segmento", "modalidade", "cliente"), carteira_minima=1e9) -> pd.DataFrame`, com as colunas: chaves + `carteira_ativa_base`, `carteira_ativa_ref`, `crescimento_pct`, `inadimplencia_base_pct`, `inadimplencia_ref_pct`, `variacao_inadimplencia_pp`
  - `correlacao_spearman(df, x, y) -> dict` (`rho`, `p_valor`, `n`)
  - `interpretar_spearman(rho, p_valor, alfa=0.05) -> str`
  - `tendencia_linear(valores) -> dict` (`inclinacao`, `ic95_inferior`, `ic95_superior`, `r2`, `p_valor`, `n`)
  - `participacao_e_hhi(fato, mes, por="segmento") -> tuple[pd.DataFrame, float]` (colunas `[por, carteira_ativa, participacao_pct]`; HHI de 0 a 10.000)
  - `classificar_hhi(hhi) -> str`
  - `descritivas_por_grupo(fato, grupo) -> pd.DataFrame` (índice = grupo; colunas `media, mediana, desvio_padrao, q1, q3, minimo, maximo, n_meses`)

- [ ] **Step 1: Escrever os testes (acrescentar ao fim de `tests/test_analysis.py`)**

```python
def test_crescimento_x_risco(fato_exemplo):
    cxr = analysis.crescimento_x_risco(fato_exemplo, "2024-12", "2025-12", chaves=("segmento", "cliente"), carteira_minima=0)
    fintech = cxr.set_index(["segmento", "cliente"]).loc[("Fintech", "PF")]
    assert fintech["crescimento_pct"] == pytest.approx(100.0)
    assert fintech["inadimplencia_base_pct"] == pytest.approx(10.0)
    assert fintech["inadimplencia_ref_pct"] == pytest.approx(15.0)
    assert fintech["variacao_inadimplencia_pp"] == pytest.approx(5.0)


def test_crescimento_x_risco_exclui_carteira_pequena(fato_exemplo):
    cxr = analysis.crescimento_x_risco(fato_exemplo, "2024-12", "2025-12", chaves=("segmento", "cliente"), carteira_minima=500)
    assert ("Fintech" in cxr["segmento"].tolist()) is False


def test_correlacao_spearman_perfeita():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})
    r = analysis.correlacao_spearman(df, "x", "y")
    assert r["rho"] == pytest.approx(1.0)
    assert r["n"] == 5


def test_correlacao_spearman_poucos_pontos():
    r = analysis.correlacao_spearman(pd.DataFrame({"x": [1, 2], "y": [2, 1]}), "x", "y")
    assert math.isnan(r["rho"]) and r["n"] == 2


def test_interpretar_spearman():
    assert "positiva" in analysis.interpretar_spearman(0.6, 0.001)
    assert "não é estatisticamente significativa" in analysis.interpretar_spearman(0.1, 0.4)


def test_tendencia_linear_reta_perfeita():
    t = analysis.tendencia_linear([1.0, 1.5, 2.0, 2.5])
    assert t["inclinacao"] == pytest.approx(0.5)
    assert t["r2"] == pytest.approx(1.0)
    assert t["ic95_inferior"] == pytest.approx(0.5)
    assert t["ic95_superior"] == pytest.approx(0.5)


def test_participacao_e_hhi(fato_exemplo):
    part, hhi = analysis.participacao_e_hhi(fato_exemplo, "2025-12")
    banco = part.set_index("segmento").loc["Banco", "participacao_pct"]
    assert banco == pytest.approx(2000 / 2200 * 100)
    assert hhi == pytest.approx((2000 / 2200 * 100) ** 2 + (200 / 2200 * 100) ** 2)


def test_classificar_hhi():
    assert analysis.classificar_hhi(1000).startswith("baixa")
    assert analysis.classificar_hhi(2000).startswith("moderada")
    assert analysis.classificar_hhi(8000).startswith("alta")


def test_descritivas_por_grupo(fato_exemplo):
    d = analysis.descritivas_por_grupo(fato_exemplo, "cliente")
    assert d.loc["PJ", "mediana"] == pytest.approx(2.0)
    assert d.loc["PJ", "n_meses"] == 2
    assert list(d.columns) == ["media", "mediana", "desvio_padrao", "q1", "q3", "minimo", "maximo", "n_meses"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_analysis.py -v`
Expected: os 10 testes antigos passam e os 9 novos falham com `AttributeError`

- [ ] **Step 3: Implementar (acrescentar ao fim de `src/analysis.py`)**

```python
def crescimento_x_risco(fato, mes_base, mes_ref, chaves=("segmento", "modalidade", "cliente"), carteira_minima=1e9):
    """Para cada combinação (ex.: Fintech × Empréstimos × PF), mede quanto a carteira cresceu
    e quanto a inadimplência mudou entre os dois meses.

    carteira_minima (R$) exclui combinações muito pequenas, em que poucos reais de
    diferença geram percentuais enormes e distorcem a análise. Padrão: R$ 1 bilhão.
    """
    chaves = list(chaves)
    colunas = ["carteira_ativa", "carteira_inadimplencia"]
    base = fato[fato["ano_mes"] == mes_base].groupby(chaves, observed=True)[colunas].sum()
    ref = fato[fato["ano_mes"] == mes_ref].groupby(chaves, observed=True)[colunas].sum()
    df = base.join(ref, lsuffix="_base", rsuffix="_ref", how="inner")
    df = df[df["carteira_ativa_base"] >= max(carteira_minima, 0.01)]

    df["crescimento_pct"] = taxa_percentual(df["carteira_ativa_ref"] - df["carteira_ativa_base"], df["carteira_ativa_base"])
    df["inadimplencia_base_pct"] = taxa_percentual(df["carteira_inadimplencia_base"], df["carteira_ativa_base"])
    df["inadimplencia_ref_pct"] = taxa_percentual(df["carteira_inadimplencia_ref"], df["carteira_ativa_ref"])
    df["variacao_inadimplencia_pp"] = df["inadimplencia_ref_pct"] - df["inadimplencia_base_pct"]
    colunas_saida = chaves + ["carteira_ativa_base", "carteira_ativa_ref", "crescimento_pct",
                              "inadimplencia_base_pct", "inadimplencia_ref_pct", "variacao_inadimplencia_pp"]
    return df.reset_index()[colunas_saida]


def correlacao_spearman(df, x, y):
    """Correlação de Spearman entre duas colunas.

    Por que Spearman e não Pearson: ele compara a ORDEM dos valores (postos), não os
    valores em si. Assim, um crescimento explosivo (ex.: +300%) não domina o resultado,
    e não é preciso supor relação linear nem distribuição normal.
    """
    dados = df[[x, y]].dropna()
    n = int(len(dados))
    if n < 3:
        return {"rho": float("nan"), "p_valor": float("nan"), "n": n}
    resultado = stats.spearmanr(dados[x], dados[y])
    return {"rho": float(resultado.statistic), "p_valor": float(resultado.pvalue), "n": n}


def interpretar_spearman(rho, p_valor, alfa=0.05):
    """Traduz o resultado para linguagem simples, sem afirmar causalidade."""
    if np.isnan(rho):
        return "Não há combinações suficientes para calcular a correlação com os filtros atuais."
    if p_valor >= alfa:
        return (f"A correlação (ρ = {rho:.2f}) não é estatisticamente significativa (p = {p_valor:.3f}): "
                "não há evidência de que crescer mais ande junto com mais risco neste recorte.")
    forca = "forte" if abs(rho) >= 0.6 else "moderada" if abs(rho) >= 0.3 else "fraca"
    sentido = "positiva" if rho > 0 else "negativa"
    leitura = ("segmentos que mais cresceram tenderam a piorar mais a inadimplência" if rho > 0
               else "segmentos que mais cresceram tenderam a piorar menos (ou melhorar) a inadimplência")
    return (f"Correlação {sentido} {forca} (ρ = {rho:.2f}, p = {p_valor:.3f}): {leitura}. "
            "Correlação não implica causalidade.")


def tendencia_linear(valores):
    """Reta de tendência (mínimos quadrados) de uma série mensal.

    A inclinação é a variação média por mês (em p.p., se a série for uma taxa em %).
    O intervalo de confiança de 95% usa a distribuição t com n-2 graus de liberdade.
    """
    y = np.asarray(list(valores), dtype=float)
    n = len(y)
    if n < 3:
        return {"inclinacao": float("nan"), "ic95_inferior": float("nan"), "ic95_superior": float("nan"),
                "r2": float("nan"), "p_valor": float("nan"), "n": n}
    reta = stats.linregress(np.arange(n), y)
    margem = stats.t.ppf(0.975, n - 2) * reta.stderr
    return {
        "inclinacao": float(reta.slope),
        "ic95_inferior": float(reta.slope - margem),
        "ic95_superior": float(reta.slope + margem),
        "r2": float(reta.rvalue ** 2),
        "p_valor": float(reta.pvalue),
        "n": n,
    }


def participacao_e_hhi(fato, mes, por="segmento"):
    """Participação de mercado (%) e índice de Herfindahl-Hirschman (HHI).

    HHI = soma dos quadrados das participações em %, de 0 (pulverizado) a 10.000
    (um único participante). Mede o quanto o crédito está concentrado.
    """
    no_mes = fato[fato["ano_mes"] == mes]
    part = no_mes.groupby(por, as_index=False, observed=True)["carteira_ativa"].sum()
    part["participacao_pct"] = taxa_percentual(part["carteira_ativa"], part["carteira_ativa"].sum())
    part = part.sort_values("participacao_pct", ascending=False).reset_index(drop=True)
    hhi = float((part["participacao_pct"] ** 2).sum())
    return part, hhi


def classificar_hhi(hhi):
    """Faixas usadas por autoridades de concorrência (Guia do CADE / DOJ-FTC)."""
    if hhi < 1500:
        return "baixa concentração (HHI < 1.500)"
    if hhi <= 2500:
        return "moderada concentração (1.500 a 2.500)"
    return "alta concentração (HHI > 2.500)"


def descritivas_por_grupo(fato, grupo):
    """Estatísticas descritivas da taxa de inadimplência MENSAL de cada grupo.

    Cada grupo (ex.: cada UF) gera uma série de meses; resumimos essa série com medidas
    de centro (média, mediana), de dispersão (desvio-padrão, quartis) e extremos.
    """
    mensal = serie_mensal(fato, por=grupo)
    g = mensal.groupby(grupo, observed=True)["taxa_inadimplencia"]
    tabela = pd.DataFrame({
        "media": g.mean(), "mediana": g.median(), "desvio_padrao": g.std(),
        "q1": g.quantile(0.25), "q3": g.quantile(0.75),
        "minimo": g.min(), "maximo": g.max(), "n_meses": g.count(),
    })
    return tabela.sort_values("mediana", ascending=False)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest -v`
Expected: todos os testes passam (25 + 19 = 44 passed)

- [ ] **Step 5: Commit**

```bash
git add src/analysis.py tests/test_analysis.py
git commit -m "adiciona correlação de Spearman, tendência linear, HHI e descritivas"
```

---

### Task 7: Notebook de EDA e imagens para o README

**Files:**
- Create: `notebooks/01_eda.ipynb` (gerado por um script temporário fora do repositório)
- Create: `outputs/*.png` (gerados ao executar o notebook)

**Interfaces:**
- Consumes: todas as funções de `src.analysis`; Parquets de `data/processed/`
- Produces: notebook executado, com as saídas visíveis no GitHub; imagens `outputs/01_evolucao.png`, `02_boxplot_uf.png`, `03_quadrante.png`, `04_participacao.png`

- [ ] **Step 1: Escrever o gerador do notebook (no scratchpad, não versionado)**

Crie o arquivo `<scratchpad>/gerar_notebook.py`, em que `<scratchpad>` é o diretório de
rascunho da sessão:
```python
"""Gera notebooks/01_eda.ipynb. Uso: python <scratchpad>/gerar_notebook.py <raiz_do_projeto>"""
import sys
from pathlib import Path

import nbformat as nbf

raiz = Path(sys.argv[1])
nb = nbf.v4.new_notebook()
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

nb.cells = [
    md("# EDA: crescimento e risco do crédito nacional (SCR.data, 2024–2025)\n\n"
       "**Pergunta orientadora:** onde o crédito brasileiro está crescendo entre 2024 e 2025, e esse "
       "crescimento vem acompanhado de mais risco?\n\n"
       "Fonte: Banco Central do Brasil, SCR.data (licença ODbL). Os dados foram preparados por "
       "`src/extract.py` e `src/transform.py`. Os indicadores vêm de `src/analysis.py` (as mesmas "
       "funções usadas pelo app)."),
    code("import sys, pathlib\n"
         "sys.path.insert(0, str(pathlib.Path.cwd().parent))  # permite importar src/\n\n"
         "import pandas as pd\nimport matplotlib.pyplot as plt\nfrom src import analysis, config\n\n"
         "pd.set_option('display.float_format', lambda v: f'{v:,.2f}')\n"
         "fato = pd.read_parquet(config.DIR_PROCESSED / 'fato_credito.parquet')\n"
         "qualidade = pd.read_parquet(config.DIR_PROCESSED / 'qualidade_mensal.parquet')\n"
         "SAIDA = config.DIR_OUTPUTS\n"
         "FONTE = 'Fonte: Banco Central do Brasil, SCR.data'\n"
         "fato.shape"),
    md("## 1. Qualidade dos dados\n\nAntes de analisar, verificamos linhas, nulos, duplicadas e combinações "
       "suprimidas por sigilo (`numero_de_operacoes = -1`) em cada arquivo mensal bruto."),
    code("qualidade"),
    code("print('Tipos das colunas:')\nprint(fato.dtypes)\n"
         "print('\\nPercentual de combinações suprimidas por mês:')\n"
         "print((qualidade['combinacoes_suprimidas'] / qualidade['linhas'] * 100).describe())"),
    md("## 2. Visão geral: evolução mensal"),
    code("total = analysis.serie_mensal(fato)\npor_cliente = analysis.serie_mensal(fato, por='cliente')\n"
         "k = analysis.kpis(fato, '2024-12', '2025-12')\nk"),
    code("fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5))\n"
         "for cliente, g in por_cliente.groupby('cliente', observed=True):\n"
         "    ax1.plot(g['ano_mes'], g['carteira_ativa'] / 1e12, marker='o', label=cliente)\n"
         "    ax2.plot(g['ano_mes'], g['taxa_inadimplencia'], marker='o', label=cliente)\n"
         "ax1.set(title='Carteira ativa por tipo de cliente', xlabel='Mês', ylabel='R$ trilhões')\n"
         "ax2.set(title='Taxa de inadimplência (> 90 dias)', xlabel='Mês', ylabel='% da carteira')\n"
         "for ax in (ax1, ax2):\n    ax.tick_params(axis='x', rotation=90)\n    ax.legend(title='Cliente')\n    ax.grid(alpha=.3)\n"
         "fig.text(0.01, -0.04, FONTE, fontsize=8)\nfig.tight_layout()\nfig.savefig(SAIDA / '01_evolucao.png', dpi=150, bbox_inches='tight')"),
    md("## 3. Estatística descritiva: inadimplência mensal por grupo\n\n"
       "Para cada grupo, resumimos os 24 meses de taxa de inadimplência com centro (média, mediana), "
       "dispersão (desvio-padrão, quartis) e extremos."),
    code("analysis.descritivas_por_grupo(fato, 'segmento')"),
    code("analysis.descritivas_por_grupo(fato, 'modalidade')"),
    code("desc_uf = analysis.descritivas_por_grupo(fato, 'uf')\ndesc_uf"),
    code("mensal_uf = analysis.serie_mensal(fato, por='uf')\nordem = desc_uf.index.tolist()\n"
         "fig, ax = plt.subplots(figsize=(13, 4.5))\n"
         "ax.boxplot([mensal_uf.loc[mensal_uf['uf'] == uf, 'taxa_inadimplencia'] for uf in ordem], tick_labels=ordem)\n"
         "ax.set(title='Distribuição da inadimplência mensal por UF (24 meses)', xlabel='UF (ordenada pela mediana)', ylabel='% da carteira')\n"
         "ax.grid(alpha=.3)\nfig.text(0.01, -0.03, FONTE, fontsize=8)\nfig.tight_layout()\n"
         "fig.savefig(SAIDA / '02_boxplot_uf.png', dpi=150, bbox_inches='tight')"),
    md("## 4. Crescimento × risco: correlação de Spearman\n\n"
       "Unidade de análise: cada combinação **tipo de instituição × modalidade × PF/PJ** com carteira de "
       "pelo menos R$ 1 bi em dez/2024. Comparamos o crescimento da carteira (dez/24 → dez/25) com a "
       "variação da inadimplência em pontos percentuais."),
    code("cxr = analysis.crescimento_x_risco(fato, '2024-12', '2025-12')\n"
         "corr = analysis.correlacao_spearman(cxr, 'crescimento_pct', 'variacao_inadimplencia_pp')\n"
         "print(corr)\nprint(analysis.interpretar_spearman(corr['rho'], corr['p_valor']))\n"
         "cxr.sort_values('carteira_ativa_ref', ascending=False).head(15)"),
    code("fig, ax = plt.subplots(figsize=(10, 6))\n"
         "for seg, g in cxr.groupby('segmento', observed=True):\n"
         "    ax.scatter(g['crescimento_pct'], g['inadimplencia_ref_pct'], s=g['carteira_ativa_ref'] / 1e10, alpha=.6, label=seg)\n"
         "ax.axvline(cxr['crescimento_pct'].median(), ls='--', c='gray')\nax.axhline(cxr['inadimplencia_ref_pct'].median(), ls='--', c='gray')\n"
         "ax.set(title='Quadrante de risco: crescimento × inadimplência (dez/2025)', xlabel='Crescimento da carteira em 12 meses (%)', ylabel='Inadimplência em dez/2025 (%)')\n"
         "ax.legend(title='Tipo de instituição', fontsize=8)\nax.grid(alpha=.3)\nfig.text(0.01, -0.03, FONTE + ' · tamanho do ponto = carteira', fontsize=8)\n"
         "fig.tight_layout()\nfig.savefig(SAIDA / '03_quadrante.png', dpi=150, bbox_inches='tight')"),
    md("## 5. Tendência temporal da inadimplência\n\nRegressão linear simples da taxa mensal. "
       "A inclinação é a variação média por mês, em p.p. Ressalva: 24 pontos é uma série curta."),
    code("for cliente, g in por_cliente.groupby('cliente', observed=True):\n"
         "    print(cliente, analysis.tendencia_linear(g['taxa_inadimplencia']))\n"
         "print('Total', analysis.tendencia_linear(total['taxa_inadimplencia']))"),
    md("## 6. Quem empresta: participação de mercado e concentração (HHI)"),
    code("part, hhi = analysis.participacao_e_hhi(fato, '2025-12')\nprint(f'HHI = {hhi:,.0f}: {analysis.classificar_hhi(hhi)}')\n"
         "seg = analysis.crescimento_x_risco(fato, '2024-12', '2025-12', chaves=('segmento',), carteira_minima=0)\n"
         "part.merge(seg[['segmento', 'crescimento_pct', 'inadimplencia_ref_pct']], on='segmento')"),
    code("fig, ax = plt.subplots(figsize=(9, 4))\nax.barh(part['segmento'].astype(str), part['participacao_pct'])\nax.invert_yaxis()\n"
         "ax.set(title='Participação na carteira ativa por tipo de instituição (dez/2025)', xlabel='% da carteira nacional', ylabel='Tipo de instituição')\n"
         "ax.set_xscale('log')\nax.grid(alpha=.3)\nfig.text(0.01, -0.04, FONTE + ' · eixo em escala logarítmica', fontsize=8)\n"
         "fig.tight_layout()\nfig.savefig(SAIDA / '04_participacao.png', dpi=150, bbox_inches='tight')"),
    md("## 7. Conclusões\n\nESCREVER APÓS EXECUTAR (ver Step 4 do plano)."),
]
nbf.write(nb, raiz / "notebooks" / "01_eda.ipynb")
print("notebook gerado")
```

- [ ] **Step 2: Gerar e executar o notebook**

```bash
python <scratchpad>/gerar_notebook.py "$PWD"
jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda.ipynb
ls -lh outputs/
```
Expected: o nbconvert termina sem erro e aparecem 4 arquivos PNG em `outputs/`.

- [ ] **Step 3: Ler os resultados**

Run: `jupyter nbconvert --to markdown --stdout notebooks/01_eda.ipynb | less`
Anote os números reais:
- KPIs
- rho, p-valor e n do Spearman
- inclinações e IC das tendências
- HHI e o crescimento por segmento
- UFs e modalidades de maior e menor mediana

Abra as 4 imagens (com a ferramenta Read) e confira se são legíveis (título, eixos, legenda, fonte).

- [ ] **Step 4: Escrever a seção 7 com os números reais**

Substitua a última célula (a "ESCREVER APÓS EXECUTAR") por um markdown com exatamente
estas três subseções. Os números vêm do Step 3; nenhum número pode ser estimado.
- **Observações (o que os dados mostram):** 4 a 6 itens, cada um com o número e a seção
  do notebook que o sustenta (ex.: "a carteira cresceu X% (seção 2)").
- **Hipóteses (possíveis explicações, não testadas aqui):** 2 a 3 itens, marcados como
  hipótese.
- **Recomendações (para o público: gestores de risco e fintechs):** 2 a 3 itens, cada um
  ligado a uma observação.
- **Limites:**
  - 24 meses
  - dados agregados, com supressão por sigilo
  - correlação não é causalidade
  - corte de R$ 1 bi no Spearman

Depois execute de novo para manter a ordem das células:
`jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda.ipynb`

- [ ] **Step 5: Commit e merge da etapa**

```bash
git add notebooks/01_eda.ipynb outputs/*.png
git commit -m "adiciona notebook de EDA com estatísticas e conclusões"
git checkout develop && git merge --no-ff feature/eda -m "integra etapa de EDA"
```

---

### Task 8: Formatação e gráficos (utils + graficos)

**Files:**
- Create: `src/utils.py`, `src/graficos.py`
- Test: `tests/test_utils.py`, `tests/test_graficos.py`

**Interfaces:**
- Consumes: saídas de `analysis.serie_mensal`, `crescimento_x_risco` e `participacao_e_hhi`
- Produces:
  - `utils.formatar_reais(valor) -> str` ("R$ 7,44 tri")
  - `utils.formatar_pct(valor, casas=2) -> str` ("5,15%")
  - `utils.formatar_pp(valor, casas=2) -> str` ("+0,12 p.p.")
  - `utils.nome_mes(ano_mes) -> str` ("dez/2025")
  - `utils.numero_br(valor, casas) -> str`
  - `utils.FONTE: str`
  - `graficos.linhas_mensais(serie, valor, titulo, rotulo_y, por=None, escala=1.0) -> go.Figure`
  - `graficos.quadrante(cxr, cor="segmento") -> go.Figure`
  - `graficos.barras(df, categoria, valor, titulo, rotulo_valor, horizontal=True, log=False) -> go.Figure`
  - `graficos.boxplot(mensal, grupo, titulo) -> go.Figure`
  - Todas as figuras trazem o título, os títulos dos eixos e uma anotação com `utils.FONTE`.

- [ ] **Step 1: Criar a branch e escrever os testes**

```bash
git checkout develop && git checkout -b feature/app
```

`tests/test_utils.py`:
```python
from src import utils


def test_formatar_reais_escalas():
    assert utils.formatar_reais(7.444e12) == "R$ 7,44 tri"
    assert utils.formatar_reais(7.4e9) == "R$ 7,40 bi"
    assert utils.formatar_reais(1.5e6) == "R$ 1,50 mi"
    assert utils.formatar_reais(1234.5) == "R$ 1.234,50"
    assert utils.formatar_reais(float("nan")) == "n/d"


def test_formatar_pct_e_pp():
    assert utils.formatar_pct(5.1478) == "5,15%"
    assert utils.formatar_pp(0.123) == "+0,12 p.p."
    assert utils.formatar_pp(-1.5) == "-1,50 p.p."
    assert utils.formatar_pct(float("nan")) == "n/d"


def test_nome_mes():
    assert utils.nome_mes("2025-12") == "dez/2025"
    assert utils.nome_mes("2024-01") == "jan/2024"
```

`tests/test_graficos.py`:
```python
import pandas as pd

from src import analysis, graficos, utils


def _tem_padrao(fig, titulo):
    assert fig.layout.title.text == titulo
    assert fig.layout.xaxis.title.text and fig.layout.yaxis.title.text
    assert any(utils.FONTE in a.text for a in fig.layout.annotations)


def test_linhas_mensais(fato_exemplo):
    serie = analysis.serie_mensal(fato_exemplo, por="cliente")
    fig = graficos.linhas_mensais(serie, "taxa_inadimplencia", "Inadimplência", "% da carteira", por="cliente")
    _tem_padrao(fig, "Inadimplência")
    assert len(fig.data) == 2


def test_quadrante(fato_exemplo):
    cxr = analysis.crescimento_x_risco(fato_exemplo, "2024-12", "2025-12", chaves=("segmento", "cliente"), carteira_minima=0)
    _tem_padrao(graficos.quadrante(cxr), "Quadrante de risco: crescimento × inadimplência")


def test_barras_e_boxplot(fato_exemplo):
    part, _ = analysis.participacao_e_hhi(fato_exemplo, "2025-12")
    _tem_padrao(graficos.barras(part, "segmento", "participacao_pct", "Participação", "% da carteira"), "Participação")
    mensal = analysis.serie_mensal(fato_exemplo, por="uf")
    _tem_padrao(graficos.boxplot(mensal, "uf", "Distribuição por UF"), "Distribuição por UF")
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_utils.py tests/test_graficos.py -v`
Expected: FAIL com `ImportError`

- [ ] **Step 3: Implementar `src/utils.py`**

```python
"""Formatação de números e textos no padrão brasileiro, para a interface."""
import math

FONTE = "Fonte: Banco Central do Brasil, SCR.data (dados abertos, licença ODbL)"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _vazio(valor) -> bool:
    return valor is None or (isinstance(valor, float) and math.isnan(valor))


def numero_br(valor: float, casas: int = 2) -> str:
    """1234.5 -> '1.234,50' (troca os separadores do padrão americano pelo brasileiro)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_reais(valor) -> str:
    """Valores grandes ficam legíveis: R$ 7,44 tri / R$ 812,30 bi / R$ 4,10 mi."""
    if _vazio(valor):
        return "n/d"
    for limite, sufixo in [(1e12, "tri"), (1e9, "bi"), (1e6, "mi")]:
        if abs(valor) >= limite:
            return f"R$ {numero_br(valor / limite)} {sufixo}"
    return f"R$ {numero_br(valor)}"


def formatar_pct(valor, casas: int = 2) -> str:
    return "n/d" if _vazio(valor) else f"{numero_br(valor, casas)}%"


def formatar_pp(valor, casas: int = 2) -> str:
    """Diferença entre duas taxas, em pontos percentuais, sempre com sinal."""
    if _vazio(valor):
        return "n/d"
    sinal = "+" if valor >= 0 else "-"
    return f"{sinal}{numero_br(abs(valor), casas)} p.p."


def nome_mes(ano_mes: str) -> str:
    """'2025-12' -> 'dez/2025'."""
    return f"{MESES[int(ano_mes[5:7]) - 1]}/{ano_mes[:4]}"
```

- [ ] **Step 4: Implementar `src/graficos.py`**

```python
"""Gráficos Plotly do app. Todo gráfico sai com título, eixos com unidade, legenda e fonte."""
import plotly.express as px
import plotly.graph_objects as go

from src import utils

PALETA = ["#1F4E9E", "#3B82C4", "#7FB3E6", "#0B2A5B", "#E07A1F", "#8C9BB0", "#2E9E8F", "#B23A48"]


def _padronizar(fig: go.Figure, titulo: str, rotulo_x: str, rotulo_y: str) -> go.Figure:
    fig.update_layout(
        title=titulo, xaxis_title=rotulo_x, yaxis_title=rotulo_y,
        template="plotly_white", colorway=PALETA, margin=dict(t=60, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
    )
    fig.add_annotation(text=utils.FONTE, xref="paper", yref="paper", x=0, y=-0.22,
                       showarrow=False, font=dict(size=10, color="#5B6B82"), xanchor="left")
    return fig


def linhas_mensais(serie, valor, titulo, rotulo_y, por=None, escala=1.0):
    """Série mensal. `escala` divide o valor (ex.: 1e9 para mostrar em R$ bilhões)."""
    dados = serie.assign(_y=serie[valor] / escala, _mes=serie["ano_mes"].map(utils.nome_mes))
    if por:
        dados[por] = dados[por].astype(str)
    fig = px.line(dados, x="_mes", y="_y", color=por, markers=True,
                  labels={"_y": rotulo_y, "_mes": "Mês", por or "": ""})
    return _padronizar(fig, titulo, "Mês", rotulo_y)


def quadrante(cxr, cor="segmento"):
    """Dispersão crescimento × inadimplência; as linhas tracejadas são as medianas."""
    rotulo = [c for c in ["segmento", "modalidade", "cliente", "uf"] if c in cxr.columns]
    dados = cxr.assign(_carteira_bi=cxr["carteira_ativa_ref"] / 1e9, **{c: cxr[c].astype(str) for c in rotulo})
    fig = px.scatter(
        dados, x="crescimento_pct", y="inadimplencia_ref_pct", size="_carteira_bi", color=cor,
        hover_data={c: True for c in rotulo} | {"_carteira_bi": ":.1f", "variacao_inadimplencia_pp": ":.2f"},
        labels={"crescimento_pct": "Crescimento da carteira (%)", "inadimplencia_ref_pct": "Inadimplência (%)",
                "_carteira_bi": "Carteira (R$ bi)", "variacao_inadimplencia_pp": "Variação da inadimplência (p.p.)"},
        size_max=45,
    )
    fig.add_vline(x=dados["crescimento_pct"].median(), line_dash="dash", line_color="gray")
    fig.add_hline(y=dados["inadimplencia_ref_pct"].median(), line_dash="dash", line_color="gray")
    return _padronizar(fig, "Quadrante de risco: crescimento × inadimplência",
                       "Crescimento da carteira no período (%)", "Inadimplência no mês final (%)")


def barras(df, categoria, valor, titulo, rotulo_valor, horizontal=True, log=False):
    dados = df.assign(**{categoria: df[categoria].astype(str)})
    eixos = dict(x=valor, y=categoria, orientation="h") if horizontal else dict(x=categoria, y=valor)
    fig = px.bar(dados, **eixos, labels={valor: rotulo_valor, categoria: ""}, log_x=log and horizontal)
    if horizontal:
        fig.update_yaxes(autorange="reversed")
        return _padronizar(fig, titulo, rotulo_valor, categoria.replace("_", " ").capitalize())
    return _padronizar(fig, titulo, categoria.replace("_", " ").capitalize(), rotulo_valor)


def boxplot(mensal, grupo, titulo):
    """Distribuição da inadimplência mensal de cada grupo, ordenada pela mediana."""
    ordem = mensal.groupby(grupo, observed=True)["taxa_inadimplencia"].median().sort_values(ascending=False).index.astype(str).tolist()
    dados = mensal.assign(**{grupo: mensal[grupo].astype(str)})
    fig = px.box(dados, x=grupo, y="taxa_inadimplencia", category_orders={grupo: ordem},
                 labels={"taxa_inadimplencia": "Inadimplência mensal (%)", grupo: grupo.upper()})
    return _padronizar(fig, titulo, grupo.upper(), "Inadimplência mensal (%)")
```

- [ ] **Step 5: Rodar e ver passar**

Run: `pytest -v`
Expected: todos passam (44 + 3 utils + 3 graficos = 50 passed)

- [ ] **Step 6: Commit**

```bash
git add src/utils.py src/graficos.py tests/test_utils.py tests/test_graficos.py
git commit -m "cria formatação brasileira e gráficos padronizados com fonte"
```

---

### Task 9: Interface base, app.py e página Início

**Files:**
- Create: `src/interface.py`, `app.py`, `pages/1_inicio.py`, `.streamlit/config.toml`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `config.DIR_PROCESSED`, `analysis.*`, `graficos.*`, `utils.*`
- Produces:
  - `interface.ARQUIVOS: dict[str, str]`
  - `interface.carregar_dados() -> dict[str, pd.DataFrame]` (chama `st.stop()` se algum Parquet faltar)
  - `interface.barra_lateral(fato) -> dict` (chaves `inicio`, `fim`, `clientes`, `segmentos`, `regioes`, `ufs`, `modalidades`)
  - `interface.contexto() -> tuple[dict, dict, pd.DataFrame]` (dados, filtros, fato filtrado)
  - `interface.aviso_filtros(filtros, fato_filtrado) -> None`
  - `interface.sem_dados(df) -> bool`
  - `interface.mostrar(fig, como_ler: str) -> None`
  - `interface.meses_comparacao(fato, filtros) -> tuple[str, str]`
  - Fixture `app_teste` em `tests/test_app.py`
- As páginas guardam os dados em `st.session_state["dados"]` e os filtros em `st.session_state["filtros"]`.

- [ ] **Step 1: Escrever o teste de fumaça do app**

`tests/test_app.py`:
```python
"""Testes de fumaça: o app abre sem erro com dados sintéticos e mostra aviso quando faltam dados."""
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src import config


@pytest.fixture
def app_teste(tmp_path, monkeypatch, fato_exemplo):
    """Grava Parquets sintéticos em uma pasta temporária e aponta o app para ela."""
    fato_exemplo.to_parquet(tmp_path / "fato_credito.parquet")
    pd.DataFrame({"ano_mes": ["2024-12", "2025-12"], "cliente": ["PF", "PF"], "carteira_ativa": [1.0, 2.0]}).to_parquet(tmp_path / "resumo_mensal.parquet")
    pd.DataFrame({"ano_mes": ["2025-12"], "cliente": ["PF"], "cnae_ocupacao": ["Assalariado"], "carteira_ativa": [1.0], "carteira_inadimplencia": [0.1]}).to_parquet(tmp_path / "fato_setor.parquet")
    pd.DataFrame({"ano_mes": ["2025-12"], "linhas": [10], "nulos": [0], "duplicadas": [0], "combinacoes_suprimidas": [1]}).to_parquet(tmp_path / "qualidade_mensal.parquet")
    monkeypatch.setattr(config, "DIR_PROCESSED", tmp_path)
    st.cache_data.clear()
    return AppTest.from_file("app.py", default_timeout=30)


def test_inicio_abre_sem_erro(app_teste):
    at = app_teste.run()
    assert not at.exception
    assert len(at.metric) == 4


def test_mensagem_quando_parquet_falta(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DIR_PROCESSED", tmp_path)
    st.cache_data.clear()
    at = AppTest.from_file("app.py", default_timeout=30).run()
    assert not at.exception
    assert any("python -m src.transform" in e.value for e in at.error)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_app.py -v`
Expected: FAIL (`app.py` não existe)

- [ ] **Step 3: Implementar `src/interface.py`**

```python
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
    segmentos = st.sidebar.multiselect("Tipo de instituição", _opcoes(fato, "segmento"), placeholder="Todos")
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
    st.caption("**Filtros ativos:** " + " · ".join(partes) + f" · **{len(fato_filtrado):,} combinações**".replace(",", "."))


def sem_dados(df: pd.DataFrame) -> bool:
    if df.empty:
        st.info("Nenhum dado para os filtros escolhidos. Amplie o período ou remova algum filtro na barra lateral.")
        return True
    return False


def mostrar(fig, como_ler: str) -> None:
    st.plotly_chart(fig, width="stretch")
    st.caption(f"**Como ler:** {como_ler}")
```

- [ ] **Step 4: Implementar `app.py`**

```python
"""Ponto de entrada do app Streamlit: Panorama do Crédito Nacional (SCR.data).

Executar:  streamlit run app.py
Os filtros da barra lateral são criados aqui, uma vez, e valem para todas as páginas.
"""
import streamlit as st

from src import interface

st.set_page_config(page_title="Panorama do Crédito Nacional", page_icon="📊", layout="wide")

dados = interface.carregar_dados()
st.session_state["dados"] = dados
st.session_state["filtros"] = interface.barra_lateral(dados["fato_credito"])

paginas = st.navigation([
    st.Page("pages/1_inicio.py", title="Início", icon="🏠", default=True),
])
paginas.run()
```

- [ ] **Step 5: Implementar `pages/1_inicio.py`**

```python
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
interface.aviso_filtros(filtros, fato)

if interface.sem_dados(fato):
    st.stop()

k = analysis.kpis(fato, mes_base, mes_ref)
comparacao = f"{utils.nome_mes(mes_base)} → {utils.nome_mes(mes_ref)}"
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Carteira ativa ({utils.nome_mes(mes_ref)})", utils.formatar_reais(k["carteira_ref"]),
          help="Saldo total das operações de crédito em dia e em atraso.")
c2.metric("Crescimento da carteira", utils.formatar_pct(k["crescimento_pct"]), help=f"Comparação {comparacao}.")
c3.metric("Inadimplência (> 90 dias)", utils.formatar_pct(k["inadimplencia_ref_pct"]),
          delta=utils.formatar_pp(k["inadimplencia_ref_pct"] - k["inadimplencia_base_pct"]), delta_color="inverse",
          help=f"Parcela da carteira vencida há mais de 90 dias. Variação {comparacao}.")
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
if not por_segmento.empty:
    lider = por_segmento.sort_values("crescimento_pct", ascending=False).iloc[0]
    achados.append(f"O tipo de instituição que mais cresceu foi **{lider['segmento']}** "
                   f"(**{utils.formatar_pct(lider['crescimento_pct'])}**), com inadimplência de "
                   f"**{utils.formatar_pct(lider['inadimplencia_ref_pct'])}**. Veja a página *Crescimento x Risco*.")
for achado in achados:
    st.markdown(f"- {achado}")

with st.expander("Por que este painel existe (aplicação profissional)"):
    st.markdown(
        "Este painel foi construído sobre o mesmo conjunto de dados de um case comercial do autor, "
        "publicado em outra tecnologia, que já gerou contratos com clientes e o interesse de duas fintechs "
        "e de uma financeira de cartões. Esta versão refaz todo o pipeline em Python e Streamlit, com o "
        "processo de dados documentado e reproduzível."
    )

st.caption("Os resultados descrevem associações nos dados agregados do BCB e não demonstram causalidade. "
           "Veja a página *Metodologia e limites*.")
```

- [ ] **Step 6: Criar `.streamlit/config.toml`**

```toml
# Tema azul e branco (identidade visual do autor)
[theme]
base = "light"
primaryColor = "#1F4E9E"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#EEF3FB"
textColor = "#0F1B2D"

[client]
toolbarMode = "minimal"
```

- [ ] **Step 7: Rodar e ver passar**

Run: `pytest tests/test_app.py -v`
Expected: 2 passed. Se aparecer aviso de parâmetro descontinuado (`width="stretch"`), confira
a assinatura com `python -c "import streamlit as st, inspect; print(inspect.signature(st.plotly_chart))"`
e use o parâmetro que a versão instalada aceita.

- [ ] **Step 8: Commit**

```bash
git add src/interface.py app.py pages/1_inicio.py .streamlit/config.toml tests/test_app.py
git commit -m "cria app com filtros globais, tema e página inicial com KPIs"
```

---

### Task 10: Páginas de análise (Evolução, Crescimento x Risco, Quem empresta, Onde e o quê, Metodologia)

**Files:**
- Create: `pages/2_evolucao.py`, `pages/3_crescimento_risco.py`, `pages/4_quem_empresta.py`, `pages/5_onde_e_o_que.py`, `pages/6_metodologia.py`
- Modify: `app.py` (lista de páginas)
- Modify: `tests/test_app.py` (acrescentar no fim)

**Interfaces:**
- Consumes: `interface.contexto`, `interface.meses_comparacao`, `interface.aviso_filtros`, `interface.sem_dados`, `interface.mostrar` (Task 9); `analysis.*` (Tasks 5–6); `graficos.*`, `utils.*` (Task 8)

- [ ] **Step 1: Escrever os testes (acrescentar ao fim de `tests/test_app.py`)**

```python
PAGINAS = ["pages/2_evolucao.py", "pages/3_crescimento_risco.py", "pages/4_quem_empresta.py",
           "pages/5_onde_e_o_que.py", "pages/6_metodologia.py"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_paginas_abrem_sem_erro(app_teste, pagina):
    at = app_teste.run()
    at.switch_page(pagina).run()
    assert not at.exception, at.exception
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_app.py -v`
Expected: os 5 testes novos falham (a página não existe ou não está registrada)

- [ ] **Step 3: Registrar as páginas no `app.py`**

Substitua o bloco `paginas = st.navigation([...])` por:
```python
paginas = st.navigation([
    st.Page("pages/1_inicio.py", title="Início", icon="🏠", default=True),
    st.Page("pages/2_evolucao.py", title="Evolução", icon="📈"),
    st.Page("pages/3_crescimento_risco.py", title="Crescimento x Risco", icon="🎯"),
    st.Page("pages/4_quem_empresta.py", title="Quem empresta", icon="🏦"),
    st.Page("pages/5_onde_e_o_que.py", title="Onde e o quê", icon="🗺️"),
    st.Page("pages/6_metodologia.py", title="Metodologia e limites", icon="📚"),
])
```

- [ ] **Step 4: `pages/2_evolucao.py`**

```python
"""Evolução mensal da carteira e da inadimplência, com a tendência estatística."""
import streamlit as st

from src import analysis, graficos, interface, utils

dados, filtros, fato = interface.contexto()
st.title("Evolução mensal")
interface.aviso_filtros(filtros, fato)
if interface.sem_dados(fato):
    st.stop()

opcoes = {"Total": None, "Tipo de cliente (PF/PJ)": "cliente", "Tipo de instituição": "segmento", "Crédito livre x direcionado": "grupo_credito"}
escolha = st.radio("Separar as linhas por", list(opcoes), horizontal=True)
por = opcoes[escolha]
serie = analysis.serie_mensal(fato, por=por)

interface.mostrar(
    graficos.linhas_mensais(serie, "carteira_ativa", "Carteira ativa por mês", "R$ bilhões", por=por, escala=1e9),
    "cada ponto é o saldo total de crédito no fim do mês. Inclinação para cima = carteira crescendo.",
)
interface.mostrar(
    graficos.linhas_mensais(serie, "taxa_inadimplencia", "Taxa de inadimplência (> 90 dias) por mês", "% da carteira", por=por),
    "percentual da carteira com atraso acima de 90 dias. Linha subindo = risco aumentando.",
)

st.subheader("Tendência da inadimplência (regressão linear)")
total = analysis.serie_mensal(fato)
t = analysis.tendencia_linear(total["taxa_inadimplencia"])
c1, c2, c3 = st.columns(3)
c1.metric("Variação média por mês", utils.formatar_pp(t["inclinacao"], 3))
c2.metric("Intervalo de confiança 95%", f"{utils.formatar_pp(t['ic95_inferior'], 3)} a {utils.formatar_pp(t['ic95_superior'], 3)}")
c3.metric("R² / p-valor", f"{utils.numero_br(t['r2'])} / {utils.numero_br(t['p_valor'], 3)}")
if t["n"] >= 3:
    significativa = t["p_valor"] < 0.05
    st.markdown(
        f"Em {t['n']} meses, a inadimplência total variou em média **{utils.formatar_pp(t['inclinacao'], 3)} por mês**. "
        + ("A tendência é estatisticamente significativa (p < 0,05)." if significativa
           else "A tendência **não** é estatisticamente significativa (p ≥ 0,05): pode ser só oscilação.")
    )
st.caption("Ressalva: a série tem no máximo 24 meses, o que é curto para tendências; a reta descreve o período e não é previsão.")
```

- [ ] **Step 5: `pages/3_crescimento_risco.py`**

```python
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
    "à direita da linha tracejada estão os segmentos que cresceram mais que a mediana; acima, os de inadimplência "
    "maior que a mediana. O quadrante superior direito concentra 'crescimento com risco'. O tamanho do ponto é a carteira.",
)

corr = analysis.correlacao_spearman(cxr, "crescimento_pct", "variacao_inadimplencia_pp")
st.subheader("O crescimento anda junto com a piora da inadimplência?")
c1, c2, c3 = st.columns(3)
c1.metric("Correlação de Spearman (ρ)", utils.numero_br(corr["rho"]) if corr["n"] >= 3 else "n/d")
c2.metric("p-valor", utils.numero_br(corr["p_valor"], 3) if corr["n"] >= 3 else "n/d")
c3.metric("Segmentos comparados", corr["n"])
st.markdown(analysis.interpretar_spearman(corr["rho"], corr["p_valor"]))
st.caption("Spearman compara a ordem dos valores (de -1 a +1). É robusto a crescimentos extremos e não supõe relação linear. "
           "Associação não é causa: crescer não 'provoca' inadimplência, e outros fatores (juros, perfil do cliente, prazo) influenciam.")

with st.expander("Tabela dos segmentos"):
    tabela = cxr.sort_values("carteira_ativa_ref", ascending=False).assign(
        carteira_ativa_ref=lambda d: d["carteira_ativa_ref"].map(utils.formatar_reais),
        crescimento_pct=lambda d: d["crescimento_pct"].map(utils.formatar_pct),
        inadimplencia_ref_pct=lambda d: d["inadimplencia_ref_pct"].map(utils.formatar_pct),
        variacao_inadimplencia_pp=lambda d: d["variacao_inadimplencia_pp"].map(utils.formatar_pp),
    )[list(chaves) + ["carteira_ativa_ref", "crescimento_pct", "inadimplencia_ref_pct", "variacao_inadimplencia_pp"]]
    st.dataframe(tabela, hide_index=True, width="stretch")
```

- [ ] **Step 6: `pages/4_quem_empresta.py`**

```python
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
st.metric(f"Concentração do mercado (HHI, {utils.nome_mes(mes_ref)})", utils.numero_br(hhi, 0), help="Soma dos quadrados das participações, de 0 a 10.000.")
st.markdown(f"Resultado: **{analysis.classificar_hhi(hhi)}**.")

log = st.toggle("Escala logarítmica", value=True, help="Útil porque os bancos são muito maiores que os demais.")
interface.mostrar(
    graficos.barras(part, "segmento", "participacao_pct", f"Participação na carteira ativa ({utils.nome_mes(mes_ref)})", "% da carteira", log=log),
    "quanto da carteira total cada tipo de instituição detém. Na escala logarítmica, cada marca do eixo é 10 vezes a anterior.",
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
            "parcela da carteira com atraso acima de 90 dias.",
        )
st.caption("A classificação 'Fintech', 'Banco' etc. é a do próprio BCB no campo 'segmento' do SCR.data.")
```

- [ ] **Step 7: `pages/5_onde_e_o_que.py`**

```python
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
            "modalidades com maior parcela em atraso acima de 90 dias.",
        )
    grupo = analysis.serie_mensal(fato, por="grupo_credito")
    interface.mostrar(
        graficos.linhas_mensais(grupo, "taxa_inadimplencia", "Inadimplência: crédito livre x direcionado", "% da carteira", por="grupo_credito"),
        "crédito direcionado (rural, imobiliário, BNDES) tem regras e juros próprios; o livre é negociado entre as partes.",
    )
```

- [ ] **Step 8: `pages/6_metodologia.py`**

```python
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
6. Validação: a carteira nacional de dez/2025 confere com o arquivo bruto (≈ R$ 7,44 tri).

### Indicadores
- **Inadimplência** = carteira vencida há mais de 90 dias ÷ carteira ativa.
- **Crescimento** = variação da carteira ativa entre o mês base (12 meses antes do fim do período, quando disponível) e o mês final.
- **HHI** = soma dos quadrados das participações de mercado (0 a 10.000).
- **Spearman** = correlação entre o crescimento e a variação da inadimplência dos segmentos.

### Limites (leia antes de concluir)
- Os dados são **agregados**: não há informação de clientes ou contratos individuais, nem de instituições específicas.
- A supressão por sigilo esconde o número de operações de combinações pequenas (o saldo continua somado).
- 24 meses é uma série curta: tendências descrevem o período e **não são previsões**.
- As análises mostram **associações**, não causas.
""")

st.subheader("Qualidade dos arquivos brutos (por mês)")
st.dataframe(dados["qualidade_mensal"], hide_index=True, width="stretch")
st.caption(utils.FONTE + ". Dicionário de dados completo em `docs/dicionario_dados.md` no repositório.")
```

- [ ] **Step 9: Rodar e ver passar**

Run: `pytest -v`
Expected: todos passam (50 + 2 + 5 = 57 passed). Se `at.switch_page` não aceitar o caminho
com `st.navigation`, troque para o formato que a versão instalada aceita (confira com
`python -c "from streamlit.testing.v1 import AppTest; help(AppTest.switch_page)"`).

- [ ] **Step 10: Conferência visual com os dados reais**

Run: `streamlit run app.py`
Abra http://localhost:8501 e verifique as 6 páginas com estes testes manuais:
- (a) Período só em 2025, com Cliente = PF.
- (b) Tipo de instituição = Fintech.
- (c) UF = AC, com Modalidade = Outros créditos, para provocar o aviso de "sem dados" ou "segmentos insuficientes".

Nenhuma página pode mostrar erro vermelho. Tire uma captura da Início e do Quadrante para
o README e salve como `outputs/app_inicio.png` e `outputs/app_quadrante.png`.

- [ ] **Step 11: Commit e merge da etapa**

```bash
git add app.py pages tests/test_app.py outputs/app_*.png
git commit -m "adiciona páginas de evolução, crescimento x risco, instituições, UF/produto e metodologia"
git checkout develop && git merge --no-ff feature/app -m "integra aplicação Streamlit"
```

---

### Task 11: Dicionário de dados e README completo

**Files:**
- Create: `docs/dicionario_dados.md`
- Create: `README.md`

**Interfaces:**
- Consumes: os números reais do notebook (Task 7, Step 3), as imagens de `outputs/` e as decisões desta especificação

- [ ] **Step 1: Criar a branch**

```bash
git checkout develop && git checkout -b docs/readme
```

- [ ] **Step 2: Gerar a base do dicionário de dados a partir dos Parquets**

```bash
python - <<'EOF'
import pandas as pd
from src import config
for nome in ["fato_credito", "fato_setor", "resumo_mensal", "qualidade_mensal"]:
    df = pd.read_parquet(config.DIR_PROCESSED / f"{nome}.parquet")
    print(f"\n## {nome} ({len(df):,} linhas)")
    for c in df.columns:
        exemplo = df[c].iloc[0]
        print(f"| `{c}` | {df[c].dtype} | {exemplo} |")
EOF
```

- [ ] **Step 3: Escrever `docs/dicionario_dados.md`**

Para cada uma das 4 tabelas, uma tabela markdown com as colunas: `Coluna | Tipo | Descrição |
Origem no CSV do BCB | Exemplo`. A saída do Step 2 dá os tipos e os exemplos. As
descrições seguem a metodologia do SCR.data:
- `carteira_ativa`: saldo total (a vencer + vencido)
- `carteira_inadimplencia`: vencido acima de 90 dias
- `ativo_problematico`: definição copiada do PDF de metodologia do SCR.data
  (`metodologia_versao2.pdf`). Ler o PDF antes de escrever e não descrever de memória.
- `combinacoes_suprimidas`: quantas linhas do CSV original tinham `numero_de_operacoes = -1`
- `grupo_credito`: derivado de `origem`
- `regiao`: derivado de `uf` (IBGE)

Termine o documento com a lista de valores possíveis de `segmento`, `cliente`, `porte` e
`modalidade`, obtida com `df[col].unique()`.

- [ ] **Step 4: Escrever `README.md` com as 16 seções obrigatórias**

Use exatamente esta estrutura de títulos. O conteúdo de cada seção está descrito abaixo.
Todos os números vêm do notebook executado (nenhum estimado).

```markdown
# Panorama do Crédito Nacional: crescimento e risco (SCR.data · 2024–2025)

> App: <LINK_STREAMLIT> · Vídeo: <LINK_VIDEO> · Projeto Final, Visualização de Dados e BI (SENAI SC / SCTEC)

## 1. Título e resumo
## 2. Problema, objetivo e importância
## 3. Escopo e resultados esperados
## 4. Fonte e autorização dos dados
## 5. Pipeline e metodologia
## 6. Bibliotecas e tecnologias
## 7. Resultados encontrados
## 8. Discussão e conclusão
## 9. Aplicação profissional
## 10. Aplicação Streamlit
## 11. Como executar
## 12. Estrutura de pastas
## 13. Limitações e melhorias futuras
## 14. Créditos e referências
## 15. Links de entrega
## 16. Estratégia de versionamento
```

O que vai em cada seção:
1. Três frases: o que é, qual dado, qual pergunta.
2. A pergunta orientadora (texto exato da especificação), o público e a relevância
   (crescimento sem controle de risco destrói valor).
3. A lista do que está dentro e fora do escopo e os critérios de conclusão (copiar da
   especificação, seção 1).
4. A tabela da seção 2 da especificação, com a frase: "Dados públicos e agregados; não há
   dados pessoais nem sensíveis (LGPD). Não foi necessária autorização, pois a licença
   ODbL permite o uso com atribuição."
5. Um diagrama Mermaid do pipeline:
   ```mermaid
   flowchart LR
     A[BCB: scrdata_2024/2025.zip] -->|src/extract.py| B[data/raw]
     B -->|src/transform.py| C[data/processed/*.parquet]
     C -->|src/analysis.py| D[notebooks/01_eda.ipynb]
     C -->|src/analysis.py| E[app.py Streamlit]
   ```
   Em seguida, as 7 decisões de tratamento (copiar a docstring de `src/transform.py`), os
   indicadores e as 4 análises estatísticas, com a justificativa de cada uma (Spearman:
   robusto; regressão: tendência com IC; HHI: concentração; descritivas: centro e
   dispersão).
6. Uma tabela `Biblioteca | Versão | Função no projeto | Documentação`, com uma linha para
   cada pacote do `requirements.txt` e do `requirements-dev.txt` e as versões fixadas.
7. Os números reais e as imagens `outputs/01_evolucao.png`, `02_boxplot_uf.png`,
   `03_quadrante.png` e `04_participacao.png`, cada uma com a legenda "como ler" e a
   resposta direta à pergunta.
8. Copiar e adaptar a seção 7 do notebook (observação / hipótese / recomendação) e
   escrever explicitamente o que NÃO pode ser concluído.
9. A validação comercial, em texto fiel ao e-mail do autor ao professor (10/10/2026): o
   case publicado (https://bcb-scr-data.andersondiroza.com.br) gerou contratos com
   clientes menores e contatos de duas fintechs e de uma financeira de cartões. Depois,
   como o pipeline seria usado numa empresa:
   - agendamento mensal, conforme a periodicidade e a defasagem informadas na página do
     dataset (conferir no portal antes de escrever)
   - validação automática do total
   - monitoramento de mudanças de layout (o ETL já falha se faltar coluna)
   - governança (dados públicos; se combinados a dados internos, entram na LGPD)
   - custos e manutenção
10. O link do deploy, uma lista das páginas com uma linha cada, os filtros e as capturas
    `outputs/app_*.png`.
11. Os comandos:
    ```bash
    git clone <repositório> && cd scr-credito-streamlit
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements-dev.txt
    python -m src.extract      # baixa ~2,4 GB do BCB (ou copie os ZIPs para data/raw/)
    python -m src.transform    # gera data/processed/*.parquet
    pytest                     # roda os testes
    streamlit run app.py
    ```
    Observação: os Parquets já estão versionados, então para só abrir o app basta
    instalar o `requirements.txt` e rodar `streamlit run app.py`. Variáveis opcionais em
    `.env.example`; não há segredos.
12. A árvore do repositório, com uma linha explicando cada pasta e cada arquivo principal.
13. Lacunas, vieses e melhorias:
    - lacunas e vieses: sigilo, dados agregados, 24 meses
    - melhorias de dados: série desde 2012, cruzamento com a Selic (API SGS do BCB)
    - melhorias técnicas: modelo preditivo de inadimplência, atualização automática via
      GitHub Actions
14. Fontes, bibliotecas, metodologia do SCR.data (links dos PDFs do BCB) e a frase:
    "Este projeto contou com o apoio do assistente de IA Claude (Anthropic) na estruturação
    do código, nos testes e na revisão da documentação. As decisões analíticas, a escolha
    do tema e a validação dos resultados são do autor."
15. Uma tabela com Repositório, Deploy, Trello, Repositório da turma, Publicação no
    LinkedIn e Vídeo no Drive, com `<a preencher>` onde ainda não houver link.
16. A estratégia de branches das Global Constraints e o porquê do `--no-ff` (preserva no
    histórico cada etapa como um bloco).

- [ ] **Step 5: Revisar o README contra o enunciado**

Confira item por item contra a seção 5.2 do enunciado (as 16 seções), a 3.1 (entregáveis)
e o e-mail do professor (dicionário de dados, validação comercial). Rode
`grep -n "—" README.md docs/dicionario_dados.md`: o resultado tem que ser vazio (sem
travessões).

- [ ] **Step 6: Commit, merge e versão estável na main**

```bash
git add README.md docs/dicionario_dados.md
git commit -m "adiciona README completo e dicionário de dados"
git checkout develop && git merge --no-ff docs/readme -m "integra documentação"
pytest
git checkout main && git merge --no-ff develop -m "publica versão 1.0 do projeto"
```

---

### Task 12: Deploy (GitHub privado + Streamlit Community Cloud)

**Files:**
- Modify: `README.md` (links da seção 15 e do topo)

**Interfaces:**
- Consumes: o repositório completo na `main`

- [ ] **Step 1: Criar o repositório privado e enviar (pedir confirmação ao autor antes)**

Esta ação publica no GitHub, então só rode depois do "ok" do autor:
```bash
gh repo create scr-credito-streamlit --private --source . --remote origin --description "Panorama do Crédito Nacional (SCR.data/BCB) em Python + Streamlit"
git push -u origin main && git push -u origin develop
```
Expected: a URL `https://github.com/andersondiroza-dev/scr-credito-streamlit`.

- [ ] **Step 2: Deploy no Streamlit (o autor faz no navegador, com orientação)**

1. Acessar https://share.streamlit.io e entrar com o GitHub (`andersondiroza-dev`),
   autorizando o acesso a repositórios privados.
2. Clicar em "Create app" → "Deploy a public app from GitHub". Preencher: repositório
   `scr-credito-streamlit`, branch `main`, arquivo `app.py`, App URL `scr-credito-nacional`.
3. Em "Advanced settings", escolher **Python 3.12**. Não há segredos a configurar.
4. Depois do deploy, nas configurações do app, deixar "Who can view this app" como
   **público** (o avaliador precisa abrir sem login).

- [ ] **Step 3: Verificar o app publicado**

Abra o link numa janela anônima. Confira as 6 páginas, os filtros e o tempo de carga.
Também pela linha de comando:
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://scr-credito-nacional.streamlit.app
```
Expected: 200 (ou 303, que é o redirecionamento do Streamlit).

- [ ] **Step 4: Dar acesso ao professor e atualizar os links**

```bash
gh api -X PUT repos/andersondiroza-dev/scr-credito-streamlit/collaborators/<usuario_github_do_professor> -f permission=pull
```
(O autor informa o usuário GitHub do professor.) Depois, preencha no README o link do
deploy e o do repositório, no topo e na seção 15.
```bash
git checkout develop && git add README.md && git commit -m "adiciona links do deploy e do repositório" \
 && git checkout main && git merge --no-ff develop -m "publica links de entrega" && git push origin main develop
```

---

### Task 13: Material de apoio para as entregas do autor (fora do repositório)

**Files:**
- Create: `~/Desktop/SCTEC/scr-credito-streamlit-apoio/roteiro_video.md`
- Create: `~/Desktop/SCTEC/scr-credito-streamlit-apoio/trello_cards.md`
- Create: `~/Desktop/SCTEC/scr-credito-streamlit-apoio/checklist_entrega.md`

- [ ] **Step 1: Roteiro do vídeo (≤ 3 min)** com as falas, seguindo os blocos de tempo do
  enunciado: 0:00–0:30, 0:30–1:00, 1:00–1:45, 1:45–2:30 e 2:30–3:00. Usar os números
  reais, mostrar uma interação do app e indicar onde acessar. Incluir a legenda do post do
  LinkedIn com as 4 marcações: @Rodrigo Garcia Brunini, @LAB365, @SENAI Santa Catarina e
  @Sistema FIESC.
- [ ] **Step 2: Cards do Trello**: uma lista por etapa do pipeline (Planejamento, ETL, EDA,
  App, Documentação, Deploy, Divulgação), com os cards correspondentes às Tasks 1–13 e as
  datas reais em que cada uma foi feita.
- [ ] **Step 3: Checklist final**:
  - repositório privado com o professor como colaborador
  - deploy público funcionando
  - repositório da turma publicado
  - vídeo no LinkedIn com as 4 marcações
  - vídeo no Drive com acesso de leitor por link
  - Trello
  - 3 links no AVA até 30/10/2026 às 22h
  - **nenhum commit depois do envio**
