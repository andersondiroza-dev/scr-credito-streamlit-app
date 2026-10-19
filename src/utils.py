"""Formatação de números e textos no padrão brasileiro, para a interface."""
import math

FONTE = "Fonte: Banco Central do Brasil, SCR.data (dados abertos, licença ODbL)"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _vazio(valor) -> bool:
    return valor is None or (isinstance(valor, float) and math.isnan(valor))


def numero_br(valor: float, casas: int = 2) -> str:
    """1234.5 -> '1.234,50' (troca os separadores do padrão americano pelo brasileiro)."""
    if _vazio(valor):
        return "n/d"
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
