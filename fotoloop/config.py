"""Configuração do FotoLoop, lida de um arquivo JSON simples."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path

SENHA_PADRAO = "TROQUE-ESTA-SENHA"


@dataclass
class Configuracao:
    # Pasta do Google Drive para computador onde chegam as fotos (FL_*.jpg, FL_*.json).
    pasta_drive: str = ""
    # Cópia de segurança independente (originais, JPEGs do projetor e banco de dados).
    pasta_backup: str = "backup"
    porta: int = 8080
    # Permite acessar o painel de outro aparelho da rede local (celular do organizador).
    acesso_na_rede: bool = False
    senha_painel: str = SENHA_PADRAO
    modo_automatico: bool = True
    tempo_fixo_segundos: int = 8
    max_lado_projetor: int = 1920
    max_novas_seguidas: int = 30
    antigas_entre_novas: int = 2
    intervalo_varredura_segundos: float = 5.0
    url_convidados: str = ""

    def validar(self) -> None:
        erros = []
        if not self.pasta_drive:
            erros.append("pasta_drive não foi preenchida")
        if not self.senha_painel or self.senha_painel == SENHA_PADRAO:
            erros.append("troque senha_painel por uma senha sua")
        if not 3 <= self.tempo_fixo_segundos <= 60:
            erros.append("tempo_fixo_segundos deve estar entre 3 e 60")
        if self.max_novas_seguidas < 1 or self.antigas_entre_novas < 1:
            erros.append("max_novas_seguidas e antigas_entre_novas devem ser maiores que zero")
        if erros:
            raise ValueError("Configuração inválida: " + "; ".join(erros))


def carregar(caminho: str | Path) -> Configuracao:
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    conhecidos = {campo.name for campo in fields(Configuracao)}
    configuracao = Configuracao(**{chave: valor for chave, valor in dados.items() if chave in conhecidos})
    configuracao.validar()
    return configuracao
