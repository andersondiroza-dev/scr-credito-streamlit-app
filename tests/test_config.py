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
