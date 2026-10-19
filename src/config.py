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
    "carteira_inadimplencia",  # saldo das operações com alguma parcela em atraso > 90 dias (metodologia BCB)
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

# Identificação acadêmica e do autor, exibida no app (topo da página Início e barra lateral).
PROJETO = {
    "curso": "Visualização de Dados e BI (Módulo 2)",
    "trabalho": "Projeto Final",
    "instituicoes": "SCTEC · SENAI/SC · LAB365",
    "autor": "Anderson Diroza",
    "professor": "Rodrigo Garcia Brunini",
    "ano": 2026,
    "linkedin": "https://www.linkedin.com/in/andersondiroza",
    "site": "https://andersondiroza.com.br",
    # Link exibido no app: o espelho público (o repositório avaliado é privado e daria 404 para visitantes).
    "repositorio": "https://github.com/andersondiroza-dev/scr-credito-streamlit-app",
}
