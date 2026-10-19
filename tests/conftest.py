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
