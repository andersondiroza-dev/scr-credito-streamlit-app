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
