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
