import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from fotoloop.apresentacao import Apresentacao, Opcoes  # noqa: E402
from fotoloop.banco import Banco  # noqa: E402
from fotoloop.servidor import ServidorFotoLoop  # noqa: E402
from fotoloop.sincronizador import Sincronizador  # noqa: E402

SENHA = "senha-de-teste"


class ServidorTest(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        raiz = Path(self._pasta.name)
        self.backup = raiz / "backup"
        (self.backup / "projetor").mkdir(parents=True)
        self.drive = raiz / "drive"
        self.drive.mkdir()
        self.banco = Banco(self.backup / "fotoloop.db")
        self.apresentacao = Apresentacao(
            self.banco,
            Opcoes(self.drive, True, 8, 30, 2, url_convidados="https://exemplo.test/"),
        )
        sincronizador = Sincronizador(self.drive, self.backup, self.banco)
        self.servidor = ServidorFotoLoop(
            ("127.0.0.1", 0), self.apresentacao, sincronizador, self.backup, RAIZ / "web", SENHA
        )
        self.url = f"http://127.0.0.1:{self.servidor.server_address[1]}"
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        self.banco.fechar()
        self._pasta.cleanup()

    def _pedido(self, caminho, dados=None, senha=None):
        cabecalhos = {}
        if senha is not None:
            cabecalhos["X-Senha"] = senha
        corpo = None
        if dados is not None:
            corpo = json.dumps(dados).encode("utf-8")
            cabecalhos["Content-Type"] = "application/json"
        pedido = urllib.request.Request(self.url + caminho, data=corpo, headers=cabecalhos,
                                        method="POST" if dados is not None else "GET")
        try:
            with urllib.request.urlopen(pedido) as resposta:
                return resposta.status, resposta.read()
        except urllib.error.HTTPError as erro:
            return erro.code, erro.read()

    def test_telao_e_painel_sao_entregues(self):
        status, corpo = self._pedido("/")
        self.assertEqual(status, 200)
        self.assertIn(b"telao.js", corpo)
        status, corpo = self._pedido("/painel")
        self.assertEqual(status, 200)
        self.assertIn(b"painel.js", corpo)

    def test_api_publica_nao_exige_senha_e_mostra_apresentacao_vazia(self):
        status, corpo = self._pedido("/api/apresentacao")
        self.assertEqual(status, 200)
        dados = json.loads(corpo)
        self.assertIsNone(dados["atual"])
        self.assertEqual(dados["total"], 0)

    def test_painel_recusa_senha_errada_ou_ausente(self):
        self.assertEqual(self._pedido("/api/painel")[0], 401)
        self.assertEqual(self._pedido("/api/painel", senha="errada")[0], 401)
        self.assertEqual(self._pedido("/api/painel", senha=SENHA)[0], 200)

    def test_controle_exige_senha(self):
        self.assertEqual(self._pedido("/api/painel/controle", {"acao": "pausar"})[0], 401)
        status, _ = self._pedido("/api/painel/controle", {"acao": "pausar"}, senha=SENHA)
        self.assertEqual(status, 200)
        self.assertTrue(self.apresentacao.fila.pausada)

    def test_arquivo_fora_da_pasta_web_nao_e_servido(self):
        status, _ = self._pedido("/telao/../fotoloop/config.py")
        self.assertEqual(status, 404)

    def test_foto_so_sai_com_nome_de_numero(self):
        status, _ = self._pedido("/fotos/projetor/..%2Fsegredo.jpg")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
