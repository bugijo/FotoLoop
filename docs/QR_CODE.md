# QR Code para os convidados

O QR Code leva à página de envio, que é o endereço `/exec` do Apps Script (veja `CONFIGURAR_APPS_SCRIPT.md`). Use sempre esse endereço, não o do GitHub Pages.

## Gerar o QR Code definitivo

Há duas formas, ambas gratuitas:

1. **Pelo painel (recomendado)**: abra `http://127.0.0.1:8080/painel`, entre com a senha e vá até **QR Code para os convidados**. O código é gerado no próprio notebook, sem serviços externos. Clique em **Imprimir QR Code**.
2. **Pelo gerador online**: use um gerador de sua preferência com o link acima. Confira no celular antes de imprimir.

Antes de imprimir, **teste** com um celular que não seja o seu, lendo o código com a câmera nativa.

## Onde colocar

- Mesas, entrada da festa e ao lado do telão.
- Tamanho mínimo recomendado: **8 × 8 cm** impresso.
- Inclua uma frase simples: "Escaneie e envie sua foto para o telão da Lúcia!"

## Quando o link muda

O link muda somente se o GitHub Pages mudar de endereço. Se isso acontecer, atualize `url_convidados` no `config/fotoloop.json` e gere um novo QR Code.

## Recebimento encerrado

Depois de encerrar o recebimento pelo painel, a página do QR Code informa que o envio foi encerrado. Não é preciso reimprimir.
