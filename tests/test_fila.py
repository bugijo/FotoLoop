import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fotoloop.fila import Fila  # noqa: E402


def percorrer(fila, disponiveis, passos):
    """Avança a apresentação `passos` vezes e devolve a sequência exibida."""
    sequencia = []
    for _ in range(passos):
        sequencia.append(fila.avancar(disponiveis, agora=0))
    return sequencia


class FilaTest(unittest.TestCase):
    def test_rodada_sem_novas_percorre_tudo_e_recomeca(self):
        disponiveis = [1, 2, 3]
        fila = Fila()
        self.assertEqual(percorrer(fila, disponiveis, 7), [1, 2, 3, 1, 2, 3, 1])
        self.assertEqual(fila.rodada, 3)

    def test_exemplo_do_enunciado_novas_primeiro_depois_retoma_011(self):
        # Apresentação na foto 010; chegam 20 novas (094 a 113).
        antigas = list(range(1, 94))  # 001..093 já existem
        fila = Fila(max_novas_seguidas=30, antigas_entre_novas=2)
        fila.registrar_chegadas(antigas)
        fila.novas.clear()  # estas já foram exibidas antes
        fila.cursor = 10
        fila.atual = 10
        fila.vistas = list(antigas)

        fila.registrar_chegadas(list(range(94, 114)))
        disponiveis = antigas + list(range(94, 114))

        sequencia = percorrer(fila, disponiveis, 21)
        self.assertEqual(sequencia[:20], list(range(94, 114)))
        self.assertEqual(sequencia[20], 11)

    def test_constante_chegada_de_novas_nao_bloqueia_as_antigas(self):
        disponiveis = list(range(1, 6))
        fila = Fila(max_novas_seguidas=5, antigas_entre_novas=2)
        fila.registrar_chegadas(disponiveis)
        fila.novas.clear()
        proximo_numero = 100
        vistas_antigas = set()
        for _ in range(200):
            disponiveis.append(proximo_numero)
            fila.registrar_chegadas([proximo_numero])
            proximo_numero += 1
            numero = fila.avancar(disponiveis, agora=0)
            if numero <= 5:
                vistas_antigas.add(numero)
        self.assertEqual(vistas_antigas, {1, 2, 3, 4, 5})

    def test_novas_nao_repetem_quando_ja_consideradas(self):
        fila = Fila()
        fila.registrar_chegadas([1, 2])
        fila.registrar_chegadas([1, 2, 3])
        self.assertEqual(fila.novas, [1, 2, 3])

    def test_foto_oculta_sai_da_fila_de_novas(self):
        fila = Fila()
        fila.registrar_chegadas([5, 6])
        self.assertEqual(fila.proxima([6]), 6)
        self.assertEqual(fila.novas, [])

    def test_sem_fotos_nao_escolhe_nada(self):
        fila = Fila()
        self.assertIsNone(fila.proxima([]))

    def test_proximas_simula_sem_alterar_a_fila(self):
        disponiveis = list(range(1, 11))
        fila = Fila()
        fila.avancar(disponiveis, agora=0)  # exibe 1
        antes = fila.para_dict()
        previstas = fila.proximas(disponiveis, 4)
        self.assertEqual(previstas, [2, 3, 4, 5])
        self.assertEqual(fila.para_dict(), antes)
        reais = [fila.avancar(disponiveis, agora=0) for _ in range(4)]
        self.assertEqual(previstas, reais)

    def test_anteriores_respeitam_fotos_disponiveis(self):
        disponiveis = [1, 2, 3, 4, 5, 6]
        fila = Fila()
        percorrer(fila, disponiveis, 6)  # exibe 1..6
        self.assertEqual(fila.anteriores(disponiveis, 4), [2, 3, 4, 5])
        self.assertEqual(fila.anteriores([1, 3, 6], 4), [1, 3])

    def test_pendentes_conta_novas_e_restante_da_rodada(self):
        disponiveis = list(range(1, 11))
        fila = Fila()
        fila.avancar(disponiveis, agora=0)  # exibe 1
        self.assertEqual(fila.pendentes(disponiveis), 9)
        fila.registrar_chegadas([11, 12])
        self.assertEqual(fila.pendentes(disponiveis + [11, 12]), 9 + 2 + 2)

    def test_estado_restaurado_continua_de_onde_parou(self):
        disponiveis = list(range(1, 8))
        fila = Fila()
        percorrer(fila, disponiveis, 3)  # exibe 1,2,3
        salvo = fila.para_dict()

        restaurada = Fila.restaurar(salvo, max_novas_seguidas=30, antigas_entre_novas=2)
        self.assertEqual(percorrer(restaurada, disponiveis, 2), [4, 5])

    def test_restaurar_sem_dados_cria_fila_nova(self):
        fila = Fila.restaurar(None, max_novas_seguidas=7, antigas_entre_novas=3)
        self.assertEqual(fila.max_novas_seguidas, 7)
        self.assertEqual(fila.antigas_entre_novas, 3)
        self.assertIsNone(fila.atual)


if __name__ == "__main__":
    unittest.main()
