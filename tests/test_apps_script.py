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

    def test_funcao_include_existe_no_codigo(self):
        codigo = ler("Code.gs")
        self.assertRegex(codigo, r"function include\(nome\)")
        self.assertIn("HtmlService.createHtmlOutputFromFile(nome).getContent()", codigo)

    def test_template_completo_expande_sem_scriptlet_restante(self):
        # Simula o que o Apps Script faz em createTemplateFromFile('Convidados').evaluate():
        # cada <?!= include('X'); ?> é trocado pelo conteúdo de X.html.
        modelo = ler("Convidados.html")
        expandido = re.sub(r"<\?!=\s*include\('([^']+)'\);\s*\?>",
                           lambda m: ler(f"{m.group(1)}.html"), modelo)
        self.assertNotIn("<?", expandido)
        self.assertNotIn("?>", expandido)
        self.assertEqual(expandido.count("<style>"), 1)
        self.assertEqual(expandido.count("<script>"), 1)
        self.assertIn("google.script.run", expandido)

    def test_arquivos_de_include_trazem_suas_proprias_tags(self):
        self.assertTrue(ler("Estilo.html").lstrip().startswith("<style>"))
        self.assertTrue(ler("Script.html").lstrip().startswith("<script>"))

    def test_modelo_principal_usa_as_inclusoes_sem_repetir_tags(self):
        modelo = ler("Convidados.html")
        self.assertIn("<?!= include('Estilo'); ?>", modelo)
        self.assertIn("<?!= include('Script'); ?>", modelo)
        self.assertNotIn("<style>", modelo)
        self.assertNotIn("<script>", modelo)

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
