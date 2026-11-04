import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
APPS = RAIZ / "apps_script"


def ler(nome):
    return (APPS / nome).read_text(encoding="utf-8")


class AppsScriptTest(unittest.TestCase):
    def test_pagina_e_servida_pelo_proprio_apps_script(self):
        codigo = ler("Code.gs")
        self.assertIn("HtmlService.createTemplateFromFile('Convidados')", codigo)
        self.assertIn("function doGet(", codigo)

    def test_sem_post_entre_dominios(self):
        codigo = ler("Code.gs")
        self.assertNotIn("function doPost(", codigo)
        self.assertNotIn("UrlFetchApp", codigo)

    def test_envio_usa_google_script_run_e_nao_fetch(self):
        script = ler("Script.html")
        self.assertIn("google.script.run", script)
        self.assertIn(".enviarFoto(pedido)", script)
        self.assertNotIn("fetch(", script)

    def test_sucesso_so_com_confirmacao_do_servidor(self):
        script = ler("Script.html")
        self.assertIn("resposta.verificado !== true", script)
        codigo = ler("Code.gs")
        self.assertIn("conferido.getSize() !== tamanhoEsperado", codigo)
        self.assertIn("verificado: true", codigo)

    def test_includes_do_template_existem(self):
        modelo = ler("Convidados.html")
        for nome in re.findall(r"include\('([^']+)'\)", modelo):
            self.assertTrue((APPS / f"{nome}.html").exists(), nome)

    @unittest.skipUnless(shutil.which("node"), "node não instalado")
    def test_sintaxe_javascript_do_apps_script(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta)
            (caminho / "codigo.js").write_text(ler("Code.gs"), encoding="utf-8")
            corpo = re.search(r"<script>(.*)</script>", ler("Script.html"), re.S).group(1)
            (caminho / "pagina.js").write_text(corpo, encoding="utf-8")
            for arquivo in ("codigo.js", "pagina.js"):
                resultado = subprocess.run(["node", "--check", str(caminho / arquivo)],
                                           capture_output=True, text=True)
                self.assertEqual(resultado.returncode, 0, resultado.stderr)


if __name__ == "__main__":
    unittest.main()
