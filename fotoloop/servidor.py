"""Servidor HTTP local (biblioteca padrão do Python): telão, painel e API."""

from __future__ import annotations

import hmac
import io
import json
import mimetypes
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .apresentacao import Apresentacao
from .sincronizador import Sincronizador

PADRAO_FOTO = re.compile(r"^\d{4}\.jpg$")


class ServidorFotoLoop(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, endereco, apresentacao: Apresentacao, sincronizador: Sincronizador,
                 pasta_backup: Path, pasta_web: Path, senha_painel: str):
        self.apresentacao = apresentacao
        self.sincronizador = sincronizador
        self.pasta_backup = pasta_backup
        self.pasta_projetor = pasta_backup / "projetor"
        self.pasta_web = pasta_web.resolve()
        self.senha_painel = senha_painel
        super().__init__(endereco, ManipuladorFotoLoop)


class ManipuladorFotoLoop(BaseHTTPRequestHandler):
    server: ServidorFotoLoop

    # ----- rotas --------------------------------------------------------------------

    def do_GET(self) -> None:
        caminho = urlsplit(self.path).path
        if caminho == "/":
            return self._arquivo(self.server.pasta_web / "telao" / "index.html")
        if caminho in ("/painel", "/painel/"):
            return self._arquivo(self.server.pasta_web / "painel" / "index.html")
        if caminho == "/api/apresentacao":
            return self._json(self.server.apresentacao.estado_publico())
        if caminho.startswith("/fotos/projetor/"):
            nome = caminho.rsplit("/", 1)[1]
            if PADRAO_FOTO.match(nome):
                return self._arquivo(self.server.pasta_projetor / nome)
            return self._erro(404, "Foto não encontrada.")
        if caminho == "/api/painel":
            if not self._autorizado():
                return
            return self._json(self.server.apresentacao.estado_painel(self.server.sincronizador.status()))
        if caminho == "/api/painel/qrcode":
            if not self._autorizado():
                return
            return self._qrcode()
        if caminho.startswith(("/telao/", "/painel/")):
            return self._arquivo_estatico(caminho.lstrip("/"))
        return self._erro(404, "Página não encontrada.")

    def do_POST(self) -> None:
        caminho = urlsplit(self.path).path
        if not self._autorizado():
            return
        try:
            dados = self._corpo_json()
        except ValueError:
            return self._json({"ok": False, "mensagem": "Pedido inválido."}, status=400)

        try:
            if caminho == "/api/painel/controle":
                return self._json(self.server.apresentacao.controle(dados))
            if caminho == "/api/painel/abrir-backup":
                return self._json(self._abrir_pasta(self.server.pasta_backup))
        except (ValueError, KeyError, TypeError) as erro:
            return self._json({"ok": False, "mensagem": str(erro)}, status=400)
        return self._erro(404, "Ação não encontrada.")

    # ----- respostas ----------------------------------------------------------------

    def _json(self, objeto: dict, status: int = 200) -> None:
        corpo = json.dumps(objeto, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _erro(self, status: int, mensagem: str) -> None:
        self._json({"ok": False, "mensagem": mensagem}, status=status)

    def _arquivo(self, caminho: Path) -> None:
        if not caminho.is_file():
            return self._erro(404, "Arquivo não encontrado.")
        tipo = mimetypes.guess_type(caminho.name)[0] or "application/octet-stream"
        conteudo = caminho.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def _arquivo_estatico(self, caminho_relativo: str) -> None:
        alvo = (self.server.pasta_web / caminho_relativo).resolve()
        if self.server.pasta_web not in alvo.parents:
            return self._erro(404, "Arquivo não encontrado.")
        return self._arquivo(alvo)

    def _qrcode(self) -> None:
        url = self.server.apresentacao.opcoes.url_convidados
        if not url:
            return self._erro(404, "Informe url_convidados no arquivo de configuração.")
        try:
            import qrcode
            from qrcode.image.svg import SvgPathImage
        except ImportError:
            return self._erro(503, "Instale o pacote qrcode (pip install -r requirements.txt).")
        buffer = io.BytesIO()
        qrcode.make(url, image_factory=SvgPathImage, box_size=10, border=2).save(buffer)
        corpo = buffer.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _abrir_pasta(self, pasta: Path) -> dict:
        pasta.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win") and hasattr(os, "startfile"):
            os.startfile(pasta)  # type: ignore[attr-defined]
            return {"ok": True, "mensagem": "Pasta de backup aberta."}
        return {"ok": True, "mensagem": f"Pasta de backup: {pasta}"}

    # ----- entrada e autorização ----------------------------------------------------

    def _corpo_json(self) -> dict:
        tamanho = int(self.headers.get("Content-Length", "0") or 0)
        if tamanho <= 0 or tamanho > 64 * 1024:
            raise ValueError("corpo vazio ou grande demais")
        dados = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        if not isinstance(dados, dict):
            raise ValueError("JSON deve ser um objeto")
        return dados

    def _autorizado(self) -> bool:
        senha_recebida = self.headers.get("X-Senha", "")
        senha = self.server.senha_painel
        if senha and hmac.compare_digest(senha_recebida.encode("utf-8"), senha.encode("utf-8")):
            return True
        self._erro(401, "Senha do painel incorreta.")
        return False

    def log_message(self, formato: str, *args) -> None:  # menos ruído no terminal
        return
