import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fotoloop.imagens import (  # noqa: E402
    HEIC_DISPONIVEL,
    ErroConversao,
    copiar_verificado,
    gerar_jpeg_projetor,
    sha256_arquivo,
)


class ImagensTest(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.pasta = Path(self._pasta.name)

    def tearDown(self):
        self._pasta.cleanup()

    def _foto(self, nome, tamanho, cor="red", orientacao=None, formato="JPEG"):
        caminho = self.pasta / nome
        imagem = Image.new("RGB", tamanho, cor)
        if orientacao is None:
            imagem.save(caminho, formato)
        else:
            exif = Image.Exif()
            exif[0x0112] = orientacao  # orientação EXIF gravada pela câmera
            imagem.save(caminho, formato, exif=exif)
        return caminho

    def test_orientacao_exif_vertical_vira_em_pe(self):
        origem = self._foto("vertical.jpg", (300, 100), orientacao=6)  # deitada no sensor, 90°
        destino = self.pasta / "saida.jpg"
        gerar_jpeg_projetor(origem, destino, max_lado=1920)
        with Image.open(destino) as resultado:
            self.assertEqual(resultado.size, (100, 300))
            self.assertEqual(resultado.format, "JPEG")

    def test_foto_horizontal_sem_exif_mantem_proporcao(self):
        origem = self._foto("horizontal.jpg", (400, 200))
        destino = self.pasta / "saida.jpg"
        gerar_jpeg_projetor(origem, destino, max_lado=1920)
        with Image.open(destino) as resultado:
            self.assertEqual(resultado.size, (400, 200))

    def test_limite_de_lado_preserva_proporcao(self):
        origem = self._foto("grande.jpg", (4000, 3000))
        destino = self.pasta / "saida.jpg"
        gerar_jpeg_projetor(origem, destino, max_lado=1920)
        with Image.open(destino) as resultado:
            self.assertEqual(resultado.size, (1920, 1440))

    def test_png_com_transparencia_vira_jpeg_sem_erro(self):
        caminho = self.pasta / "transparente.png"
        Image.new("RGBA", (50, 50), (0, 0, 0, 0)).save(caminho)
        destino = self.pasta / "saida.jpg"
        gerar_jpeg_projetor(caminho, destino)
        with Image.open(destino) as resultado:
            self.assertEqual(resultado.mode, "RGB")

    def test_arquivo_corrompido_vira_erro_controlado(self):
        caminho = self.pasta / "corrompida.jpg"
        caminho.write_bytes(b"\xff\xd8\xff not really a jpeg" * 20)
        with self.assertRaises(ErroConversao):
            gerar_jpeg_projetor(caminho, self.pasta / "saida.jpg")
        self.assertFalse((self.pasta / "saida.jpg").exists())

    @unittest.skipUnless(HEIC_DISPONIVEL, "pillow-heif não instalado")
    def test_heic_de_iphone_vira_jpeg_com_orientacao(self):
        origem = self.pasta / "iphone.heic"
        exif = Image.Exif()
        exif[0x0112] = 6
        # O pillow-heif grava o EXIF a partir dos bytes, como nas fotos reais do iPhone.
        Image.new("RGB", (320, 120), "green").save(origem, "HEIF", exif=exif.tobytes())
        destino = self.pasta / "saida.jpg"
        gerar_jpeg_projetor(origem, destino, max_lado=1920)
        with Image.open(destino) as resultado:
            self.assertEqual(resultado.size, (120, 320))

    def test_copia_verificada_confere_hash(self):
        origem = self._foto("original.jpg", (80, 60))
        destino = self.pasta / "copia" / "original.jpg"
        copiar_verificado(origem, destino)
        self.assertEqual(sha256_arquivo(origem), sha256_arquivo(destino))


if __name__ == "__main__":
    unittest.main()
