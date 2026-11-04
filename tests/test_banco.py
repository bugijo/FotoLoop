import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fotoloop.banco import Banco  # noqa: E402


class BancoTest(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.caminho = Path(self._pasta.name) / "fotoloop.db"
        self.banco = Banco(self.caminho)

    def tearDown(self):
        self.banco.fechar()
        self._pasta.cleanup()

    def test_numeros_sao_sequenciais_e_nao_se_repetem(self):
        n1, criada1 = self.banco.registrar("FL_a")
        n2, criada2 = self.banco.registrar("FL_b")
        self.assertEqual((n1, n2), (1, 2))
        self.assertTrue(criada1 and criada2)

    def test_registro_repetido_nao_duplica(self):
        n1, _ = self.banco.registrar("FL_a", nome_original="IMG_1.HEIC")
        n2, criada = self.banco.registrar("FL_a")
        self.assertEqual(n1, n2)
        self.assertFalse(criada)
        self.assertEqual(len(self.banco.todas()), 1)

    def test_so_fotos_prontas_e_nao_ocultas_entram_na_apresentacao(self):
        a, _ = self.banco.registrar("FL_a")
        b, _ = self.banco.registrar("FL_b")
        c, _ = self.banco.registrar("FL_c")
        self.banco.atualizar(a, status="pronta")
        self.banco.atualizar(b, status="pronta")
        self.banco.atualizar(c, status="falha_conversao")
        self.assertEqual(self.banco.numeros_prontos(), [a, b])

        self.banco.ocultar(a, True)
        self.assertEqual(self.banco.numeros_prontos(), [b])
        self.assertTrue(self.banco.obter(a)["oculta"])

    def test_campos_fora_da_lista_sao_recusados(self):
        numero, _ = self.banco.registrar("FL_a")
        with self.assertRaises(ValueError):
            self.banco.atualizar(numero, numero=99)

    def test_estado_sobrevive_a_reabertura(self):
        self.banco.gravar_estado("fila", {"atual": 7, "novas": [9]})
        self.banco.registrar("FL_a")
        self.banco.fechar()

        reaberto = Banco(self.caminho)
        try:
            self.assertEqual(reaberto.ler_estado("fila"), {"atual": 7, "novas": [9]})
            self.assertEqual(reaberto.registrar("FL_a")[0], 1)
            self.assertEqual(reaberto.registrar("FL_b")[0], 2)
        finally:
            reaberto.fechar()
        self.banco = Banco(self.caminho)  # para o tearDown fechar uma conexão válida

    def test_estado_inexistente_devolve_padrao(self):
        self.assertEqual(self.banco.ler_estado("nada", {"x": 1}), {"x": 1})


if __name__ == "__main__":
    unittest.main()
