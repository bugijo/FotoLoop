import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fotoloop.velocidade import duracao_automatica, duracao_segundos  # noqa: E402


class VelocidadeAdaptativaTest(unittest.TestCase):
    def test_faixas_do_enunciado(self):
        self.assertEqual(duracao_automatica(0), 10)
        self.assertEqual(duracao_automatica(10), 10)
        self.assertEqual(duracao_automatica(11), 8)
        self.assertEqual(duracao_automatica(14), 8)
        self.assertEqual(duracao_automatica(15), 5)
        self.assertEqual(duracao_automatica(49), 5)
        self.assertEqual(duracao_automatica(50), 3)
        self.assertEqual(duracao_automatica(500), 3)

    def test_modo_fixo_ignora_pendentes(self):
        self.assertEqual(duracao_segundos(False, 12, 500), 12)
        self.assertEqual(duracao_segundos(True, 12, 500), 3)


if __name__ == "__main__":
    unittest.main()
