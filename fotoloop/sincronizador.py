"""Recebe as fotos sincronizadas pelo Google Drive para computador e cria a cópia de segurança.

Garantias:
- Cada foto recebe um número (0001, 0002...) único e permanente, guardado no banco.
- O original é copiado para uma pasta separada do Google Drive e verificado por hash.
- Fotos já registradas não são processadas de novo (reinício e reconexão são seguros).
- Falhas de conversão não interrompem o processo: a foto fica de fora do telão.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .banco import Banco
from .imagens import EXTENSOES_IMAGEM, ErroConversao, copiar_verificado, gerar_jpeg_projetor

NOME_CONTROLE = "_controle.json"
TAMANHO_MAXIMO_LOCAL = 25 * 1024 * 1024
PREFIXO_FOTO = "FL_"


def arquivo_estavel(tamanho_anterior: int | None, tamanho_atual: int) -> bool:
    """Um arquivo só é lido quando o tamanho não mudou entre duas varreduras (download concluído)."""
    return tamanho_atual > 0 and tamanho_anterior == tamanho_atual


def ler_recebimento(pasta: str | Path) -> bool:
    """Lê se o recebimento está aberto. Sem arquivo de controle, o padrão é aberto."""
    try:
        dados = json.loads((Path(pasta) / NOME_CONTROLE).read_text(encoding="utf-8"))
        return bool(dados.get("recebendo", True))
    except (OSError, ValueError, AttributeError):
        return True


def gravar_recebimento(pasta: str | Path, aberto: bool) -> None:
    """Grava o controle que o Apps Script lê pelo Google Drive."""
    destino = Path(pasta) / NOME_CONTROLE
    temporario = destino.with_name(destino.name + ".tmp")
    temporario.write_text(json.dumps({"recebendo": bool(aberto)}), encoding="utf-8")
    os.replace(temporario, destino)


class Sincronizador:
    def __init__(
        self,
        pasta_drive: str | Path,
        pasta_backup: str | Path,
        banco: Banco,
        max_lado_projetor: int = 1920,
        ao_registrar: Callable[[int], None] | None = None,
    ):
        self.pasta_drive = Path(pasta_drive)
        self.pasta_backup = Path(pasta_backup)
        self.banco = banco
        self.max_lado_projetor = max_lado_projetor
        self.ao_registrar = ao_registrar
        self.ultima_varredura: str = ""
        self.erro: str = ""
        self._tamanhos_anteriores: dict[Path, int] = {}

    def varrer(self) -> int:
        """Procura fotos novas na pasta do Drive. Devolve quantas foram processadas."""
        self.ultima_varredura = datetime.now().isoformat(timespec="seconds")
        if not self.pasta_drive.is_dir():
            self.erro = f"pasta do Google Drive não encontrada: {self.pasta_drive}"
            return 0
        self.erro = ""

        processadas = 0
        tamanhos_atuais: dict[Path, int] = {}
        identificadores_vistos: set[str] = set()

        for arquivo in sorted(self.pasta_drive.iterdir()):
            if not self._e_foto(arquivo):
                continue
            try:
                tamanho = arquivo.stat().st_size
            except OSError:
                continue
            tamanhos_atuais[arquivo] = tamanho
            identificador = arquivo.stem
            identificadores_vistos.add(identificador)

            registro = self.banco.por_identificador(identificador)
            if registro is not None and registro["status"] != "pendente":
                continue  # já sincronizada: não baixa nem processa de novo
            if not arquivo_estavel(self._tamanhos_anteriores.get(arquivo), tamanho):
                continue
            try:
                self._processar(identificador, arquivo)
                processadas += 1
            except OSError as falha:
                self.erro = f"{arquivo.name}: {falha}"

        # Fotos que ficaram pendentes (ex.: queda de energia no meio) são retomadas da cópia de segurança.
        for registro in self.banco.com_status("pendente"):
            if registro["identificador"] in identificadores_vistos:
                continue
            try:
                self._processar(registro["identificador"], None)
                processadas += 1
            except OSError as falha:
                self.erro = f"{registro['identificador']}: {falha}"

        self._tamanhos_anteriores = tamanhos_atuais
        return processadas

    def status(self) -> dict:
        return {
            "pasta_drive_encontrada": self.pasta_drive.is_dir(),
            "ultima_varredura": self.ultima_varredura,
            "erro": self.erro,
        }

    def _e_foto(self, arquivo: Path) -> bool:
        return (
            arquivo.is_file()
            and arquivo.name.startswith(PREFIXO_FOTO)
            and arquivo.suffix.lower() in EXTENSOES_IMAGEM
        )

    def _processar(self, identificador: str, origem: Path | None) -> None:
        metadados = self._ler_metadados(identificador)
        numero, _ = self.banco.registrar(
            identificador,
            nome_original=metadados.get("nome_original", identificador),
            id_drive=metadados.get("id_drive", ""),
        )
        registro = self.banco.obter(numero)
        extensao = (origem.suffix if origem else Path(registro["arquivo_original"] or "x.jpg").suffix).lower()

        pasta_originais = self.pasta_backup / "originais"
        destino = pasta_originais / f"{numero:04d}_{identificador}{extensao}"
        if not destino.exists():
            if origem is None or not origem.exists():
                raise OSError("original não encontrado para a foto pendente")
            copiar_verificado(origem, destino)
            self._copiar_metadados(identificador, numero)

        status, motivo, arquivo_projetor = self._gerar_projetor(numero, destino)

        self.banco.atualizar(
            numero,
            status=status,
            motivo=motivo,
            nome_original=metadados.get("nome_original", identificador),
            id_drive=metadados.get("id_drive", ""),
            arquivo_original=destino.relative_to(self.pasta_backup).as_posix(),
            arquivo_projetor=arquivo_projetor,
        )
        if status == "pronta" and self.ao_registrar is not None:
            self.ao_registrar(numero)

    def _gerar_projetor(self, numero: int, original: Path) -> tuple[str, str, str]:
        destino = self.pasta_backup / "projetor" / f"{numero:04d}.jpg"
        if original.stat().st_size > TAMANHO_MAXIMO_LOCAL:
            return "falha_conversao", "arquivo maior que o limite local", ""
        try:
            gerar_jpeg_projetor(original, destino, self.max_lado_projetor)
        except ErroConversao as erro:
            return "falha_conversao", str(erro), ""
        return "pronta", "", destino.relative_to(self.pasta_backup).as_posix()

    def _ler_metadados(self, identificador: str) -> dict:
        caminho = self.pasta_drive / f"{identificador}.json"
        try:
            return json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _copiar_metadados(self, identificador: str, numero: int) -> None:
        origem = self.pasta_drive / f"{identificador}.json"
        if origem.exists():
            destino = self.pasta_backup / "originais" / f"{numero:04d}_{identificador}.json"
            copiar_verificado(origem, destino)
