# Prova de funcionamento (checklist)

Este documento registra o que foi **executado** e o que depende de testes **manuais** com celulares, Google e projetor. Nada aqui é marcado como testado se não foi executado.

## Automatizado (executado no desenvolvimento)

Comando: `python -m unittest discover -s tests -t .`

| Área | Testes | Resultado |
|---|---|---|
| Velocidade adaptativa (faixas 10/8/5/3 s; modo fixo) | 2 | executado: OK |
| Fila inteligente: rodada, prioridade para novas, anti-bloqueio, persistência | 11 | executado: OK |
| Apresentação: layout 4+1+4, miniaturas reais, pausa, ocultar, velocidade, reinício, prioridade para novas | 15 | executado: OK |
| Banco: numeração, duplicações, ocultar, estado persistido | 6 | executado: OK |
| Sincronização: estabilidade, não baixar de novo, reinício, reconexão, arquivos inválidos, controle de recebimento | 10 | executado: OK |
| Imagens: orientação EXIF (JPEG e HEIC), proporção, PNG com transparência, corrompido, cópia verificada | 7 | executado: OK |
| Servidor: senha do painel, rotas, caminhos seguros | 6 | executado: OK |

Total: **57 testes, todos aprovados** na última execução (cerca de 12 s).

Teste de fumaça com o servidor real (`run.py`) e fotos de exemplo: sincronização, numeração, JPEG do projetor, API do telão, senha do painel, QR Code e controle de recebimento. Executado: OK.

Página dos convidados, executada no navegador em largura de celular (375 px): layout, prévia de foto, recusa de arquivo que não é imagem, aviso de página não configurada. Executado: OK.

Protocolo de envio: a página foi testada contra um receptor **simulado** (não é o Apps Script). Ele recebeu `text/plain` com os campos `nome`, `tipo`, `tamanho`, `sha256` e `dados`, com assinatura JPEG e hash corretos. Executado: OK.

GitHub Pages publicado: `https://bugijo.github.io/FotoLoop/web/convidados/` responde 200. A página ainda não envia fotos até `config.js` receber a URL do Apps Script.

## Manual (ainda não executado)

### Fase 1 — prova funcional

- [ ] Publicar o Apps Script conforme `CONFIGURAR_APPS_SCRIPT.md`.
- [ ] Preencher `web/convidados/config.js` com a URL `/exec` e publicar no GitHub Pages.
- [ ] Abrir a página no **iPhone** e enviar uma foto real (HEIC).
- [ ] Abrir a página num **Android** (ou Xiaomi) e enviar uma foto real (JPEG).
- [ ] Confirmar que a foto aparece na pasta **FotoLoop - Lucia 60 anos** do Drive.
- [ ] Confirmar que a mesma foto não entra em duplicidade ao reenviar.
- [ ] Testar um arquivo inválido (um PDF ou um texto renomeado) e ver a mensagem.
- [ ] Testar o encerramento do recebimento pelo painel e ver a página bloquear.

### Fase 2 — telão básico

- [ ] No notebook Windows, instalar o Drive para computador com a pasta em **Disponível offline**.
- [ ] Ver a foto de teste aparecer no telão.
- [ ] Testar o projetor por HDMI em tela cheia.

### Fase 3 — backup e offline

- [ ] Desconectar a internet e confirmar que o telão continua.
- [ ] Reconectar e confirmar que a foto nova chega e entra no telão.
- [ ] Reiniciar o notebook no meio da apresentação e confirmar que a posição é retomada.

### Fase 4–5 — apresentação e painel

- [ ] Enviar 20 fotos seguidas e confirmar que as novas aparecem primeiro e a sequência antiga volta de onde parou.
- [ ] Ocultar uma foto pelo painel e confirmar que ela sai do telão.
- [ ] Testar o painel num celular na mesma rede (`acesso_na_rede: true`).

### Fase 6 — validação final

- [ ] Teste de concorrência: 10 celulares enviando ao mesmo tempo (limite de 150 envios por 10 minutos).
- [ ] Teste com fotos de 10 a 12 MB (limite do receptor).
- [ ] Teste de 1 hora de telão contínuo, com fotos chegando.

## Limitações conhecidas (a validar)

- O cabeçalho CORS das respostas do Apps Script é aceito pelos navegadores atuais. Confirme no celular real (primeiro item da Fase 1).
- A conversão de HEIC no notebook depende do `pillow-heif`. Ele foi testado no Linux, mas não no Windows.
