import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fotoloop.apresentacao import Apresentacao, Opcoes  # noqa: E402
from fotoloop.banco import Banco  # noqa: E402
from fotoloop.config import SENHA_PADRAO, Configuracao  # noqa: E402


class Relogio:
    def __init__(self):
        self.agora = 1000.0

    def __call__(self):
        return self.agora


class ApresentacaoTest(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.raiz = Path(self._pasta.name)
        self.banco = Banco(self.raiz / "fotoloop.db")
        self.relogio = Relogio()
        self.opcoes = Opcoes(
            pasta_drive=self.raiz / "drive",
            modo_automatico=False,
            tempo_fixo_segundos=5,
            max_novas_seguidas=30,
            antigas_entre_novas=2,
            url_convidados="https://exemplo.test/convidados/",
        )
        self.apresentacao = Apresentacao(self.banco, self.opcoes, relogio=self.relogio)

    def tearDown(self):
        self.banco.fechar()
        self._pasta.cleanup()

    def _adicionar_fotos(self, quantidade):
        for indice in range(quantidade):
            numero, _ = self.banco.registrar(f"FL_{indice:03d}")
            self.banco.atualizar(numero, status="pronta")
            self.apresentacao.registrar_pronta(numero)
        return quantidade

    def test_comeca_sozinha_quando_chega_a_primeira_foto(self):
        self.assertIsNone(self.apresentacao.estado_publico()["atual"])
        self._adicionar_fotos(3)
        atual = self.apresentacao.estado_publico()["atual"]
        self.assertEqual(atual["numero"], "0001")

    def test_troca_a_foto_quando_o_tempo_acaba(self):
        self._adicionar_fotos(3)
        self.apresentacao.estado_publico()  # exibe 0001
        self.relogio.agora += 4
        self.assertEqual(self.apresentacao.estado_publico()["atual"]["numero"], "0001")
        self.relogio.agora += 1
        self.assertEqual(self.apresentacao.estado_publico()["atual"]["numero"], "0002")

    def test_layout_4_mais_1_mais_4_com_poucas_fotos_se_adapta(self):
        self._adicionar_fotos(3)
        estado = self.apresentacao.estado_publico()
        self.assertEqual(len(estado["anteriores"]), 0)
        # Com 3 fotos a sequência volta ao início: as miniaturas continuam mostrando a ordem real.
        self.assertEqual([f["numero"] for f in estado["proximas"]], ["0002", "0003", "0001", "0002"])
        self.assertEqual(estado["total"], 3)

    def test_miniaturas_correspondem_a_sequencia_real(self):
        self._adicionar_fotos(12)
        self.apresentacao.estado_publico()
        previstas = [f["numero"] for f in self.apresentacao.estado_publico()["proximas"]]
        reais = []
        for _ in range(4):
            self.relogio.agora += 5
            reais.append(f"{self.apresentacao.estado_publico()['atual']['numero']}")
        self.assertEqual(previstas, reais)

    def test_pausar_mantem_a_foto_e_continuar_reinicia_o_tempo(self):
        self._adicionar_fotos(3)
        self.apresentacao.estado_publico()
        self.apresentacao.controle({"acao": "pausar"})
        self.relogio.agora += 60
        self.assertEqual(self.apresentacao.estado_publico()["atual"]["numero"], "0001")
        self.apresentacao.controle({"acao": "continuar"})
        self.relogio.agora += 4
        self.assertEqual(self.apresentacao.estado_publico()["atual"]["numero"], "0001")

    def test_avancar_manualmente(self):
        self._adicionar_fotos(3)
        self.apresentacao.estado_publico()
        self.apresentacao.controle({"acao": "avancar"})
        self.assertEqual(self.apresentacao.estado_publico()["atual"]["numero"], "0002")

    def test_ocultar_foto_atual_tira_da_tela_na_hora(self):
        self._adicionar_fotos(3)
        self.apresentacao.estado_publico()
        self.apresentacao.controle({"acao": "ocultar", "numero": 1, "oculta": True})
        estado = self.apresentacao.estado_publico()
        self.assertEqual(estado["atual"]["numero"], "0002")
        self.assertEqual(estado["total"], 2)
        self.assertNotIn("0001", [f["numero"] for f in estado["proximas"]])

    def test_velocidade_automatica_depende_de_pendentes(self):
        self._adicionar_fotos(60)
        self.apresentacao.controle({"acao": "velocidade", "modo_automatico": True})
        self.assertEqual(self.apresentacao.estado_publico()["duracao_ms"], 3000)
        self.apresentacao.controle({"acao": "velocidade", "modo_automatico": False, "tempo_fixo_segundos": 12})
        self.assertEqual(self.apresentacao.estado_publico()["duracao_ms"], 12000)

    def test_velocidade_fora_do_limite_e_recusada(self):
        with self.assertRaises(ValueError):
            self.apresentacao.controle({"acao": "velocidade", "tempo_fixo_segundos": 1})

    def test_acao_desconhecida_e_recusada(self):
        with self.assertRaises(ValueError):
            self.apresentacao.controle({"acao": "apagar_tudo"})

    def test_estado_sobrevive_a_reinicio_do_programa(self):
        self._adicionar_fotos(10)
        self.apresentacao.estado_publico()
        self.apresentacao.controle({"acao": "avancar"})
        self.apresentacao.controle({"acao": "velocidade", "modo_automatico": False, "tempo_fixo_segundos": 7})
        posicao = self.apresentacao.estado_publico()["atual"]["numero"]
        self.banco.fechar()

        self.banco = Banco(self.raiz / "fotoloop.db")
        reiniciada = Apresentacao(self.banco, self.opcoes, relogio=self.relogio)
        estado = reiniciada.estado_publico()
        self.assertEqual(estado["atual"]["numero"], posicao)
        self.assertEqual(estado["duracao_ms"], 7000)

    def test_nova_foto_tem_prioridade_e_sequencia_retomada(self):
        self._adicionar_fotos(10)
        self.apresentacao.estado_publico()
        for _ in range(9):  # chega até a 10
            self.relogio.agora += 5
            self.apresentacao.estado_publico()
        self.assertEqual(self.apresentacao.estado_publico()["atual"]["numero"], "0010")

        for indice in range(10, 13):
            numero, _ = self.banco.registrar(f"FL_{indice:03d}")
            self.banco.atualizar(numero, status="pronta")
            self.apresentacao.registrar_pronta(numero)

        exibidas = []
        for _ in range(4):
            self.relogio.agora += 5
            exibidas.append(self.apresentacao.estado_publico()["atual"]["numero"])
        self.assertEqual(exibidas[:3], ["0011", "0012", "0013"])

    def test_painel_inclui_falhas_e_fotos_ocultas(self):
        self._adicionar_fotos(2)
        ruim, _ = self.banco.registrar("FL_ruim")
        self.banco.atualizar(ruim, status="falha_conversao", motivo="arquivo corrompido")
        painel = self.apresentacao.estado_painel({"pasta_drive_encontrada": True})
        self.assertEqual(painel["recebidas"], 3)
        self.assertEqual(painel["falhas"], [{"numero": ruim, "motivo": "arquivo corrompido"}])
        self.assertEqual(painel["url_convidados"], "https://exemplo.test/convidados/")


class ConfiguracaoTest(unittest.TestCase):
    def test_senha_padrao_e_recusada(self):
        with self.assertRaises(ValueError):
            Configuracao(pasta_drive="x", senha_painel=SENHA_PADRAO).validar()

    def test_configuracao_valida_passa(self):
        Configuracao(pasta_drive="x", senha_painel="segredo-do-evento").validar()


if __name__ == "__main__":
    unittest.main()
