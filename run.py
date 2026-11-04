#!/usr/bin/env python3
"""Inicia o telão do FotoLoop: sincronização das fotos, fila da apresentação e servidor local."""

from __future__ import annotations

import argparse
import logging
import sys
import threading
import time
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from fotoloop.apresentacao import Apresentacao, Opcoes  # noqa: E402
from fotoloop.banco import Banco  # noqa: E402
from fotoloop.config import carregar  # noqa: E402
from fotoloop.servidor import ServidorFotoLoop  # noqa: E402
from fotoloop.sincronizador import Sincronizador  # noqa: E402


def principal(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FotoLoop — telão de fotos ao vivo")
    parser.add_argument("--config", default=str(RAIZ / "config" / "fotoloop.json"),
                        help="arquivo de configuração (padrão: config/fotoloop.json)")
    parser.add_argument("--abrir", action="store_true", help="abre o telão no navegador")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    caminho_config = Path(args.config)
    if not caminho_config.exists():
        print(f"Arquivo de configuração não encontrado: {caminho_config}")
        print("Copie config/fotoloop.exemplo.json para config/fotoloop.json e preencha os campos.")
        return 1
    try:
        config = carregar(caminho_config)
    except ValueError as erro:
        print(erro)
        return 1

    pasta_backup = Path(config.pasta_backup)
    if not pasta_backup.is_absolute():
        pasta_backup = RAIZ / pasta_backup
    (pasta_backup / "originais").mkdir(parents=True, exist_ok=True)
    (pasta_backup / "projetor").mkdir(parents=True, exist_ok=True)

    banco = Banco(pasta_backup / "fotoloop.db")
    apresentacao = Apresentacao(
        banco,
        Opcoes(
            pasta_drive=Path(config.pasta_drive),
            modo_automatico=config.modo_automatico,
            tempo_fixo_segundos=config.tempo_fixo_segundos,
            max_novas_seguidas=config.max_novas_seguidas,
            antigas_entre_novas=config.antigas_entre_novas,
            url_convidados=config.url_convidados,
        ),
    )
    sincronizador = Sincronizador(
        config.pasta_drive,
        pasta_backup,
        banco,
        max_lado_projetor=config.max_lado_projetor,
        ao_registrar=apresentacao.registrar_pronta,
    )

    def laco_de_sincronizacao() -> None:
        while True:
            try:
                novas = sincronizador.varrer()
                if novas:
                    logging.info("%d foto(s) sincronizada(s)", novas)
            except Exception:  # o telão continua mesmo que algo falhe na sincronização
                logging.exception("Falha na sincronização")
            time.sleep(config.intervalo_varredura_segundos)

    threading.Thread(target=laco_de_sincronizacao, name="sincronizacao", daemon=True).start()

    host = "0.0.0.0" if config.acesso_na_rede else "127.0.0.1"
    servidor = ServidorFotoLoop(
        (host, config.porta),
        apresentacao,
        sincronizador,
        pasta_backup,
        RAIZ / "web",
        config.senha_painel,
    )
    url_telao = f"http://127.0.0.1:{config.porta}/"
    print(f"Telão: {url_telao}")
    print(f"Painel do organizador: {url_telao}painel")
    if args.abrir:
        webbrowser.open(url_telao)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nFotoLoop encerrado.")
    finally:
        servidor.server_close()
        banco.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
