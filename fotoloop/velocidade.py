"""Duração de cada fotografia no telão."""

from __future__ import annotations


def duracao_automatica(pendentes: int) -> int:
    """Segundos por foto conforme a quantidade de fotos pendentes na rodada."""
    if pendentes <= 10:
        return 10
    if pendentes <= 14:
        return 8
    if pendentes <= 49:
        return 5
    return 3


def duracao_segundos(modo_automatico: bool, tempo_fixo: int, pendentes: int) -> int:
    return duracao_automatica(pendentes) if modo_automatico else tempo_fixo
