"""Coordena a apresentação: fila, velocidade, controles do painel e estado persistido."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .banco import Banco
from .fila import Fila
from .sincronizador import gravar_recebimento, ler_recebimento
from .velocidade import duracao_segundos

CHAVE_FILA = "fila"
CHAVE_VELOCIDADE = "velocidade"


@dataclass
class Opcoes:
    pasta_drive: Path
    modo_automatico: bool
    tempo_fixo_segundos: int
    max_novas_seguidas: int
    antigas_entre_novas: int
    url_convidados: str = ""


class Apresentacao:
    def __init__(
        self,
        banco: Banco,
        opcoes: Opcoes,
        relogio: Callable[[], float] = time.time,
    ):
        self.banco = banco
        self.opcoes = opcoes
        self.relogio = relogio
        self.lock = threading.RLock()

        velocidade = banco.ler_estado(CHAVE_VELOCIDADE, {})
        self.modo_automatico = bool(velocidade.get("modo_automatico", opcoes.modo_automatico))
        self.tempo_fixo_segundos = int(velocidade.get("tempo_fixo_segundos", opcoes.tempo_fixo_segundos))
        self.fila = Fila.restaurar(
            banco.ler_estado(CHAVE_FILA),
            max_novas_seguidas=opcoes.max_novas_seguidas,
            antigas_entre_novas=opcoes.antigas_entre_novas,
        )

    # ----- ligação com o sincronizador ---------------------------------------------

    def registrar_pronta(self, numero: int) -> None:
        with self.lock:
            self.fila.registrar_chegadas([numero])
            self._salvar()

    # ----- avanço automático --------------------------------------------------------

    def atualizar(self) -> None:
        """Avança a foto quando o tempo acabou. Chamado a cada consulta do telão."""
        with self.lock:
            agora = self.relogio()
            disponiveis = self.banco.numeros_prontos()
            if self.fila.atual is None:
                # Começa sozinha assim que houver fotos; o botão "iniciar" só destrava após pausa.
                if disponiveis and not self.fila.pausada:
                    self.fila.avancar(disponiveis, agora)
                    self._salvar()
                return
            if self.fila.atual not in disponiveis:
                # Foto ocultada ou removida: sai da tela imediatamente, mesmo se pausada.
                self.fila.avancar(disponiveis, agora)
                self._salvar()
                return
            if self.fila.pausada:
                return
            if agora - self.fila.iniciada_em >= self._duracao(disponiveis):
                self.fila.avancar(disponiveis, agora)
                self._salvar()

    def _duracao(self, disponiveis: list[int]) -> float:
        return duracao_segundos(
            self.modo_automatico,
            self.tempo_fixo_segundos,
            self.fila.pendentes(disponiveis),
        )

    # ----- dados para o telão e o painel ---------------------------------------------

    def estado_publico(self) -> dict:
        self.atualizar()
        with self.lock:
            disponiveis = self.banco.numeros_prontos()
            return {
                "atual": self._foto(self.fila.atual),
                "anteriores": [self._foto(n) for n in self.fila.anteriores(disponiveis, 4)],
                "proximas": [self._foto(n) for n in self.fila.proximas(disponiveis, 4)],
                "duracao_ms": int(self._duracao(disponiveis) * 1000),
                "inicio_ms": int(self.fila.iniciada_em * 1000),
                "pausada": self.fila.pausada,
                "total": len(disponiveis),
                "rodada": self.fila.rodada,
                "recebendo": ler_recebimento(self.opcoes.pasta_drive),
            }

    def estado_painel(self, sincronizador_status: dict) -> dict:
        publico = self.estado_publico()
        with self.lock:
            disponiveis = self.banco.numeros_prontos()
            fotos = self.banco.todas()
            return {
                **publico,
                "modo_automatico": self.modo_automatico,
                "tempo_fixo_segundos": self.tempo_fixo_segundos,
                "pendentes": self.fila.pendentes(disponiveis),
                "novas_na_fila": len(self.fila.novas),
                "recebidas": len(fotos),
                "falhas": [
                    {"numero": f["numero"], "motivo": f["motivo"]}
                    for f in fotos if f["status"] == "falha_conversao"
                ],
                "fotos": [
                    {
                        "numero": f["numero"],
                        "nome_original": f["nome_original"],
                        "status": f["status"],
                        "oculta": f["oculta"],
                        "url": f"/fotos/projetor/{f['numero']:04d}.jpg",
                    }
                    for f in fotos
                ],
                "sincronizacao": sincronizador_status,
                "url_convidados": self.opcoes.url_convidados,
            }

    def _foto(self, numero: int | None) -> dict | None:
        if numero is None:
            return None
        return {"numero": f"{numero:04d}", "url": f"/fotos/projetor/{numero:04d}.jpg"}

    # ----- controles do painel ------------------------------------------------------

    def controle(self, dados: dict) -> dict:
        acao = dados.get("acao")
        with self.lock:
            agora = self.relogio()
            disponiveis = self.banco.numeros_prontos()

            if acao == "iniciar":
                self.fila.pausada = False
                if self.fila.atual not in disponiveis:
                    self.fila.avancar(disponiveis, agora)
            elif acao == "pausar":
                self.fila.pausada = True
            elif acao == "continuar":
                self.fila.pausada = False
                if self.fila.atual is None:
                    self.fila.avancar(disponiveis, agora)
                else:
                    self.fila.iniciada_em = agora
            elif acao == "avancar":
                self.fila.avancar(disponiveis, agora)
            elif acao == "velocidade":
                self.modo_automatico = bool(dados.get("modo_automatico", self.modo_automatico))
                tempo = int(dados.get("tempo_fixo_segundos", self.tempo_fixo_segundos))
                if not 3 <= tempo <= 60:
                    raise ValueError("O tempo fixo deve estar entre 3 e 60 segundos.")
                self.tempo_fixo_segundos = tempo
                self.banco.gravar_estado(
                    CHAVE_VELOCIDADE,
                    {"modo_automatico": self.modo_automatico, "tempo_fixo_segundos": tempo},
                )
            elif acao == "ocultar":
                numero = int(dados["numero"])
                self.banco.ocultar(numero, bool(dados.get("oculta", True)))
                if self.fila.atual == numero:
                    self.fila.avancar(self.banco.numeros_prontos(), agora)
            elif acao == "recebimento":
                gravar_recebimento(self.opcoes.pasta_drive, bool(dados["aberto"]))
            else:
                raise ValueError(f"Ação desconhecida: {acao!r}")

            self._salvar()
            return {"ok": True}

    def _salvar(self) -> None:
        self.banco.gravar_estado(CHAVE_FILA, self.fila.para_dict())
