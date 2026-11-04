"""Fila inteligente da apresentação.

Regras:
- Fotos novas entram em uma fila própria e são exibidas primeiro, em ordem de chegada.
- A sequência original (rodada) continua de onde parou; ao terminar, começa outra rodada.
- Para que uma sequência contínua de novas não bloqueie as antigas, depois de
  `max_novas_seguidas` novas são exibidas `antigas_entre_novas` fotos antigas.
- Todo o estado é serializável, para retomar após reinício.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field

CAMPOS_DA_CONFIGURACAO = {"max_novas_seguidas", "antigas_entre_novas"}


@dataclass
class Fila:
    max_novas_seguidas: int = 30
    antigas_entre_novas: int = 2
    atual: int | None = None
    cursor: int = 0
    rodada: int = 1
    novas: list[int] = field(default_factory=list)
    vistas: list[int] = field(default_factory=list)
    historico: list[int] = field(default_factory=list)
    bloco_novas: int = 0
    antigas_devidas: int = 0
    pausada: bool = False
    iniciada_em: float = 0.0

    # ----- entrada de fotos novas -------------------------------------------------

    def registrar_chegadas(self, numeros: list[int]) -> None:
        """Coloca na fila de novas as fotos que ainda não foram consideradas."""
        for numero in sorted(numeros):
            if numero not in self.vistas:
                self.vistas.append(numero)
                self.novas.append(numero)

    # ----- escolha da próxima foto ------------------------------------------------

    def proxima(self, disponiveis: list[int]) -> int | None:
        """Escolhe a próxima foto e atualiza o estado. Não usa a lista de disponíveis sem validar."""
        disp = sorted(set(disponiveis))
        self.novas = [numero for numero in self.novas if numero in set(disp)]

        if self.antigas_devidas == 0 and self.novas and self.bloco_novas >= self.max_novas_seguidas:
            self.antigas_devidas = self.antigas_entre_novas

        if self.novas and self.antigas_devidas == 0:
            self.bloco_novas += 1
            return self.novas.pop(0)

        antiga = self._proxima_antiga(disp)
        if antiga is None:
            if self.novas:
                self.bloco_novas += 1
                return self.novas.pop(0)
            return None

        if self.antigas_devidas > 0:
            self.antigas_devidas -= 1
            if self.antigas_devidas == 0:
                self.bloco_novas = 0
        else:
            self.bloco_novas = 0
        return antiga

    def _proxima_antiga(self, disp: list[int]) -> int | None:
        if not disp:
            return None
        for numero in disp:
            if numero > self.cursor:
                self.cursor = numero
                return numero
        self.rodada += 1
        self.cursor = disp[0]
        return disp[0]

    def avancar(self, disponiveis: list[int], agora: float) -> int | None:
        if self.atual is not None:
            self.historico.append(self.atual)
            del self.historico[:-50]
        self.atual = self.proxima(disponiveis)
        self.iniciada_em = agora
        return self.atual

    def proximas(self, disponiveis: list[int], quantidade: int = 4) -> list[int]:
        """Mostra as próximas fotos sem alterar a fila real (miniaturas da direita)."""
        simulada = copy.deepcopy(self)
        saida = []
        for _ in range(quantidade):
            numero = simulada.proxima(disponiveis)
            if numero is None:
                break
            saida.append(numero)
        return saida

    def anteriores(self, disponiveis: list[int], quantidade: int = 4) -> list[int]:
        validas = set(disponiveis)
        return [numero for numero in self.historico if numero in validas][-quantidade:]

    def pendentes(self, disponiveis: list[int]) -> int:
        """Fotos ainda não exibidas nesta rodada, somadas às novas aguardando."""
        disp = set(disponiveis)
        restantes = sum(1 for numero in disp if numero > self.cursor)
        if restantes == 0:
            restantes = len(disp)
        return restantes + sum(1 for numero in self.novas if numero in disp)

    # ----- persistência -----------------------------------------------------------

    def para_dict(self) -> dict:
        dados = asdict(self)
        for chave in CAMPOS_DA_CONFIGURACAO:
            dados.pop(chave)
        return dados

    @classmethod
    def restaurar(cls, dados: dict | None, max_novas_seguidas: int, antigas_entre_novas: int) -> "Fila":
        fila = cls(max_novas_seguidas=max_novas_seguidas, antigas_entre_novas=antigas_entre_novas)
        if not dados:
            return fila
        for chave, valor in dados.items():
            if chave in cls.__dataclass_fields__ and chave not in CAMPOS_DA_CONFIGURACAO:
                setattr(fila, chave, valor)
        return fila
