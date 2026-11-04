# Instalação e uso no Windows (notebook do evento)

Testado em desenvolvimento no Linux Mint. Ainda **não** foi executado num notebook Windows 10/11 real: os passos abaixo são o roteiro de instalação, e a checagem final está em [PROVA_FUNCIONAL.md](PROVA_FUNCIONAL.md).

## 1. Instalar o que é necessário (uma vez)

1. **Python 3.12** em <https://www.python.org/downloads/windows/>. Na instalação, marque **Add python.exe to PATH**.
2. **Google Drive para computador** em <https://www.google.com/drive/download/>. Entre com a conta do proprietário.
3. Copie a pasta do FotoLoop para o notebook (por exemplo `C:\FotoLoop`). Use o repositório <https://github.com/bugijo/FotoLoop> (botão **Code → Download ZIP**) e extraia.

## 2. Configurar o Google Drive para computador

1. No Google Drive para computador, abra as configurações e confirme que a pasta **FotoLoop - Lucia 60 anos** aparece em **Meu Drive** (ela fica em `G:\Meu Drive\...` ou na letra indicada pelo programa).
2. Clique com o botão direito na pasta e escolha **Disponibilizar offline** (ou **Manter sempre neste dispositivo**). Isso é **essencial**: sem isso, o Windows pode guardar só um atalho e não a foto em si.
3. Confirme a letra e o caminho da pasta. Eles vão para o arquivo de configuração.

## 3. Preencher a configuração

1. Dê dois cliques em **instalar_windows.bat**. Ele cria `config\fotoloop.json` e abre o Bloco de Notas.
2. Preencha:
   - `pasta_drive`: o caminho da pasta do Drive. Exemplo: `G:\\Meu Drive\\FotoLoop - Lucia 60 anos`
   - `pasta_backup`: uma pasta **fora** do Drive. Exemplo: `C:\\FotoLoop\\backup`
   - `senha_painel`: uma senha sua (não use a do exemplo)
   - `url_convidados`: `https://bugijo.github.io/FotoLoop/web/convidados/`
3. Salve e feche.

As barras invertidas precisam ser duplas (`\\`) dentro do JSON.

## 4. Abrir o telão

1. Conecte o notebook ao projetor por HDMI. Use **Win + P** e escolha **Duplicar** (ou **Estender**, se preferir o painel do organizador no notebook).
2. Dê dois cliques em **iniciar_telao.bat**.
   - Na primeira vez ele cria o ambiente e instala as dependências. Precisa de internet.
   - Abrirá o telão em `http://127.0.0.1:8080/`.
3. No navegador do projetor, pressione **F11** para tela cheia.
4. Para o painel do organizador, abra `http://127.0.0.1:8080/painel` no notebook (ou no celular, se `acesso_na_rede` for `true` e o celular estiver na mesma rede).

Deixe a janela do terminal aberta. Fechá-la encerra o telão.

## 5. Durante a festa

- O painel mostra quantas fotos chegaram, quantas estão pendentes e o estado da sincronização.
- **Pausar / Continuar / Avançar** controlam a apresentação.
- **Velocidade automática** segue as faixas da regra (10, 8, 5 ou 3 segundos). Desmarque para fixar um tempo.
- **Ocultar** tira uma foto do telão. O original continua no backup.
- **Alternar recebimento** abre ou encerra o envio.
- Com internet caindo, o telão continua com as fotos já copiadas. O painel mostra um aviso discreto.

## 6. Internet compartilhada do celular

O FotoLoop não depende do Wi-Fi do local. Basta o notebook ter internet para o Drive sincronizar. As fotos já copiadas ficam disponíveis mesmo sem internet. Quando a conexão voltar, o Drive envia as fotos pendentes e o FotoLoop as inclui automaticamente.

## Problemas comuns

| Sintoma | O que fazer |
|---|---|
| "Python nao encontrado" | Reinstale o Python marcando **Add python.exe to PATH** |
| Tela preta no telão | Ainda não há fotos prontas. Envie uma foto de teste |
| "Pasta do Google Drive NÃO encontrada" no painel | Confirme o caminho em `pasta_drive` e se o Drive para computador está conectado |
| Foto aparece no Drive mas não no telão | Veja "Fotos que não puderam ser convertidas" no painel. HEIC exige o pacote `pillow-heif` (já incluído no `requirements.txt`) |
| Telão não aparece em tela cheia | Pressione F11 na janela do navegador do projetor |
| Notebook entrou em suspensão no meio da festa | Em **Configurações → Sistema → Energia**, defina "Nunca" suspender ao usar energia da tomada |
