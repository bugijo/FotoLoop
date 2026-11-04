import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fotoloop.banco import Banco  # noqa: E402
from fotoloop.sincronizador import (  # noqa: E402
    Sincronizador,
    arquivo_estavel,
    gravar_recebimento,
    ler_recebimento,
)


class SincronizadorTest(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        raiz = Path(self._pasta.name)
        self.drive = raiz / "drive"
        self.backup = raiz / "backup"
        self.drive.mkdir()
        self.backup.mkdir()
        (self.backup / "originais").mkdir()
        (self.backup / "projetor").mkdir()
        self.banco = Banco(self.backup / "fotoloop.db")
        self.registradas = []
        self.sincronizador = Sincronizador(
            self.drive, self.backup, self.banco, max_lado_projetor=800,
            ao_registrar=self.registradas.append,
        )

    def tearDown(self):
        self.banco.fechar()
        self._pasta.cleanup()

    def _foto_drive(self, identificador, cor="blue", tamanho=(120, 90), extensao=".jpg"):
        caminho = self.drive / f"{identificador}{extensao}"
        Image.new("RGB", tamanho, cor).save(caminho, "JPEG")
        (self.drive / f"{identificador}.json").write_text(
            json.dumps({"identificador": identificador, "nome_original": f"IMG_{identificador}.HEIC",
                        "id_drive": f"id-{identificador}"}),
            encoding="utf-8",
        )
        return caminho

    def _varrer_duas_vezes(self):
        """A primeira varredura só observa o tamanho; a segunda confirma que o arquivo está completo."""
        self.sincronizador.varrer()
        return self.sincronizador.varrer()

    def test_arquivo_so_e_processado_quando_estabiliza(self):
        self._foto_drive("FL_aaa")
        self.assertEqual(self.sincronizador.varrer(), 0)
        self.assertEqual(self.sincronizador.varrer(), 1)

    def test_fotos_recebem_numeros_em_ordem_e_geram_backup(self):
        self._foto_drive("FL_bbb")
        self._foto_drive("FL_aaa")
        self._varrer_duas_vezes()

        fotos = self.banco.todas()
        self.assertEqual([f["identificador"] for f in fotos], ["FL_aaa", "FL_bbb"])
        self.assertEqual([f["numero"] for f in fotos], [1, 2])
        self.assertTrue(all(f["status"] == "pronta" for f in fotos))
        self.assertTrue((self.backup / "projetor" / "0001.jpg").exists())
        self.assertTrue((self.backup / "originais" / "0001_FL_aaa.jpg").exists())
        self.assertTrue((self.backup / "originais" / "0001_FL_aaa.json").exists())
        self.assertEqual(fotos[0]["nome_original"], "IMG_FL_aaa.HEIC")
        self.assertEqual(fotos[0]["id_drive"], "id-FL_aaa")
        self.assertEqual(self.registradas, [1, 2])

    def test_foto_ja_sincronizada_nao_e_processada_de_novo(self):
        self._foto_drive("FL_ccc")
        self._varrer_duas_vezes()
        self.registradas.clear()

        self.assertEqual(self.sincronizador.varrer(), 0)
        self.assertEqual(self.sincronizador.varrer(), 0)
        self.assertEqual(self.registradas, [])
        self.assertEqual(len(self.banco.todas()), 1)

    def test_reinicio_continua_numeracao_sem_repetir(self):
        self._foto_drive("FL_ddd")
        self._varrer_duas_vezes()
        self.banco.fechar()

        self.banco = Banco(self.backup / "fotoloop.db")
        self.sincronizador = Sincronizador(self.drive, self.backup, self.banco, 800, self.registradas.append)
        self._foto_drive("FL_eee")
        self._varrer_duas_vezes()
        numeros = [f["numero"] for f in self.banco.todas()]
        self.assertEqual(numeros, [1, 2])

    def test_arquivo_invalido_nao_interrompe_as_outras(self):
        ruim = self.drive / "FL_ruim.jpg"
        ruim.write_bytes(b"isto nao e uma imagem" * 50)
        self._foto_drive("FL_boa")
        self._varrer_duas_vezes()

        status = {f["identificador"]: f["status"] for f in self.banco.todas()}
        self.assertEqual(status["FL_ruim"], "falha_conversao")
        self.assertEqual(status["FL_boa"], "pronta")
        # FL_boa vem antes de FL_ruim em ordem alfabética, então recebe o número 0001.
        self.assertEqual(self.registradas, [1])
        self.assertEqual(self.banco.numeros_prontos(), [1])

    def test_arquivo_que_nao_e_foto_e_ignorado(self):
        (self.drive / "FL_nota.txt").write_text("oi")
        (self.drive / "_controle.json").write_text("{}")
        self._varrer_duas_vezes()
        self.assertEqual(self.banco.todas(), [])

    def test_pasta_do_drive_ausente_so_registra_erro(self):
        self.sincronizador.pasta_drive = self.drive / "nao-existe"
        self.assertEqual(self.sincronizador.varrer(), 0)
        self.assertIn("não encontrada", self.sincronizador.status()["erro"])
        self.assertFalse(self.sincronizador.status()["pasta_drive_encontrada"])

    def test_foto_pendente_e_retomada_da_copia_de_seguranca(self):
        # Simula queda de energia depois da cópia do original e antes da conversão.
        self._foto_drive("FL_fff")
        original = self.backup / "originais" / "0001_FL_fff.jpg"
        original.parent.mkdir(exist_ok=True)
        (self.drive / "FL_fff.jpg").replace(original)
        numero, _ = self.banco.registrar("FL_fff", arquivo_original="originais/0001_FL_fff.jpg")
        self.assertEqual(numero, 1)

        self.sincronizador.varrer()
        self.assertEqual(self.banco.obter(1)["status"], "pronta")
        self.assertEqual(self.registradas, [1])

    def test_arquivo_estavel_exige_tamanho_igual_e_nao_vazio(self):
        self.assertFalse(arquivo_estavel(None, 100))
        self.assertFalse(arquivo_estavel(50, 100))
        self.assertFalse(arquivo_estavel(0, 0))
        self.assertTrue(arquivo_estavel(100, 100))


class RecebimentoTest(unittest.TestCase):
    def test_controle_grava_e_le_o_estado(self):
        with tempfile.TemporaryDirectory() as pasta:
            self.assertTrue(ler_recebimento(pasta))  # sem arquivo: aberto
            gravar_recebimento(pasta, False)
            self.assertFalse(ler_recebimento(pasta))
            gravar_recebimento(pasta, True)
            self.assertTrue(ler_recebimento(pasta))


if __name__ == "__main__":
    unittest.main()
