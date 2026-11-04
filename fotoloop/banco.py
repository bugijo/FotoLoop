"""Registro das fotografias e do estado da apresentação (SQLite, sem dependências extras)."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS fotos (
    numero INTEGER PRIMARY KEY,
    identificador TEXT NOT NULL UNIQUE,
    nome_original TEXT NOT NULL DEFAULT '',
    id_drive TEXT NOT NULL DEFAULT '',
    arquivo_original TEXT NOT NULL DEFAULT '',
    arquivo_projetor TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    motivo TEXT NOT NULL DEFAULT '',
    oculta INTEGER NOT NULL DEFAULT 0,
    registrada_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS estado (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
"""

CAMPOS_ATUALIZAVEIS = {
    "status",
    "motivo",
    "nome_original",
    "id_drive",
    "arquivo_original",
    "arquivo_projetor",
}


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Banco:
    """Guarda uma linha por fotografia. O número (0001, 0002...) é definido aqui e nunca muda."""

    def __init__(self, caminho: str | Path):
        self._trava = threading.RLock()
        self._conexao = sqlite3.connect(str(caminho), check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        # WAL: uma queda de energia não deixa o banco corrompido; "NORMAL" evita um fsync a cada gravação.
        self._conexao.execute("PRAGMA journal_mode=WAL")
        self._conexao.execute("PRAGMA synchronous=NORMAL")
        self._conexao.executescript(SCHEMA)

    def fechar(self) -> None:
        with self._trava:
            self._conexao.close()

    def registrar(
        self,
        identificador: str,
        nome_original: str = "",
        id_drive: str = "",
        arquivo_original: str = "",
    ) -> tuple[int, bool]:
        """Devolve (numero, criado). Se o identificador já existe, devolve o número existente."""
        with self._trava:
            linha = self._conexao.execute(
                "SELECT numero FROM fotos WHERE identificador = ?", (identificador,)
            ).fetchone()
            if linha is not None:
                return linha["numero"], False
            numero = self._conexao.execute(
                "SELECT COALESCE(MAX(numero), 0) + 1 FROM fotos"
            ).fetchone()[0]
            self._conexao.execute(
                "INSERT INTO fotos (numero, identificador, nome_original, id_drive, "
                "arquivo_original, status, registrada_em) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (numero, identificador, nome_original, id_drive, arquivo_original, "pendente", _agora()),
            )
            self._conexao.commit()
            return numero, True

    def atualizar(self, numero: int, /, **campos: Any) -> None:
        invalidos = set(campos) - CAMPOS_ATUALIZAVEIS
        if invalidos:
            raise ValueError(f"Campos não atualizáveis: {sorted(invalidos)}")
        if not campos:
            return
        atribuicoes = ", ".join(f"{campo} = ?" for campo in campos)
        with self._trava:
            self._conexao.execute(
                f"UPDATE fotos SET {atribuicoes} WHERE numero = ?", (*campos.values(), numero)
            )
            self._conexao.commit()

    def ocultar(self, numero: int, oculta: bool) -> None:
        with self._trava:
            self._conexao.execute(
                "UPDATE fotos SET oculta = ? WHERE numero = ?", (1 if oculta else 0, numero)
            )
            self._conexao.commit()

    def obter(self, numero: int) -> dict | None:
        with self._trava:
            linha = self._conexao.execute("SELECT * FROM fotos WHERE numero = ?", (numero,)).fetchone()
        return self._para_dict(linha) if linha else None

    def por_identificador(self, identificador: str) -> dict | None:
        with self._trava:
            linha = self._conexao.execute(
                "SELECT * FROM fotos WHERE identificador = ?", (identificador,)
            ).fetchone()
        return self._para_dict(linha) if linha else None

    def com_status(self, status: str) -> list[dict]:
        with self._trava:
            linhas = self._conexao.execute(
                "SELECT * FROM fotos WHERE status = ? ORDER BY numero", (status,)
            ).fetchall()
        return [self._para_dict(linha) for linha in linhas]

    def todas(self) -> list[dict]:
        with self._trava:
            linhas = self._conexao.execute("SELECT * FROM fotos ORDER BY numero").fetchall()
        return [self._para_dict(linha) for linha in linhas]

    def numeros_prontos(self) -> list[int]:
        """Fotos que podem ser exibidas: convertidas e não ocultas."""
        with self._trava:
            linhas = self._conexao.execute(
                "SELECT numero FROM fotos WHERE status = 'pronta' AND oculta = 0 ORDER BY numero"
            ).fetchall()
        return [linha["numero"] for linha in linhas]

    def ler_estado(self, chave: str, padrao: Any = None) -> Any:
        with self._trava:
            linha = self._conexao.execute("SELECT valor FROM estado WHERE chave = ?", (chave,)).fetchone()
        return json.loads(linha["valor"]) if linha else padrao

    def gravar_estado(self, chave: str, valor: Any) -> None:
        with self._trava:
            self._conexao.execute(
                "INSERT INTO estado (chave, valor) VALUES (?, ?) "
                "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
                (chave, json.dumps(valor)),
            )
            self._conexao.commit()

    @staticmethod
    def _para_dict(linha: sqlite3.Row) -> dict:
        dados = dict(linha)
        dados["oculta"] = bool(dados["oculta"])
        return dados
