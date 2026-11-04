"""Conversão das fotos para JPEG de exibição e cópias verificadas."""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

from PIL import Image, ImageOps

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


class ErroConversao(Exception):
    """A foto não pôde ser convertida. Ela é ignorada no telão, mas o original é preservado."""


def registrar_suporte_heic() -> bool:
    """Ativa a leitura de HEIC/HEIF (iPhone) quando o pacote pillow-heif está instalado."""
    try:
        from pillow_heif import register_heif_opener
    except ImportError:
        return False
    register_heif_opener()
    return True


HEIC_DISPONIVEL = registrar_suporte_heic()


def _para_rgb(imagem: Image.Image) -> Image.Image:
    if imagem.mode == "RGB":
        return imagem
    if imagem.mode in ("RGBA", "LA") or (imagem.mode == "P" and "transparency" in imagem.info):
        rgba = imagem.convert("RGBA")
        fundo = Image.new("RGB", rgba.size, (255, 255, 255))
        fundo.paste(rgba, mask=rgba.split()[-1])
        return fundo
    return imagem.convert("RGB")


def gerar_jpeg_projetor(origem: str | Path, destino: str | Path, max_lado: int = 1920) -> None:
    """Gera um JPEG com a orientação EXIF aplicada, proporção preservada e tamanho limitado."""
    origem = Path(origem)
    destino = Path(destino)
    temporario = destino.with_name(destino.name + ".tmp")
    try:
        with Image.open(origem) as bruta:
            bruta.load()  # força a leitura completa: arquivo corrompido falha aqui
            imagem = ImageOps.exif_transpose(bruta)
            imagem = _para_rgb(imagem)
            imagem.thumbnail((max_lado, max_lado), Image.Resampling.LANCZOS)
            destino.parent.mkdir(parents=True, exist_ok=True)
            imagem.save(temporario, "JPEG", quality=90, optimize=True)
        os.replace(temporario, destino)
    except Exception as erro:  # qualquer falha de leitura vira erro controlado
        if temporario.exists():
            temporario.unlink()
        raise ErroConversao(f"{type(erro).__name__}: {erro}"[:200]) from erro


def sha256_arquivo(caminho: str | Path) -> str:
    digest = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            digest.update(bloco)
    return digest.hexdigest()


def copiar_verificado(origem: str | Path, destino: str | Path) -> None:
    """Copia o arquivo e confirma, pelo hash, que a cópia é idêntica à original."""
    origem = Path(origem)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(destino.name + ".tmp")
    shutil.copyfile(origem, temporario)
    if sha256_arquivo(temporario) != sha256_arquivo(origem):
        temporario.unlink()
        raise OSError(f"cópia de {origem.name} não confere com o original")
    os.replace(temporario, destino)
