# Configurar o Google Apps Script e o Google Drive

Esta etapa é feita **uma vez**, com a conta Google do proprietário (a mesma do Google Drive onde as fotos vão ficar). Não é preciso pagar nada.

## 1. Criar a pasta do evento e o projeto de script

1. Abra <https://script.google.com> com a conta Google do proprietário.
2. Clique em **Novo projeto**. Renomeie para `FotoLoop`.
3. Apague o conteúdo do arquivo `Código.gs` que aparece.
4. Copie **todo** o conteúdo de [`apps_script/Code.gs`](../apps_script/Code.gs) e cole ali.
5. Abra **Configurações do projeto** (ícone de engrenagem) e marque **Mostrar o arquivo de manifesto appsscript.json**. Volte a **Editor**, abra `appsscript.json` e substitua o conteúdo pelo de [`apps_script/appsscript.json`](../apps_script/appsscript.json). Salve (Ctrl+S).

## 2. Criar a pasta privada no Drive

1. No editor, na lista de funções (menu superior), escolha **configurarPastaDoEvento** e clique em **Executar**.
2. Na primeira execução o Google pede autorização. Clique em **Revisar permissões**, escolha a conta do proprietário e autorize o acesso ao Drive.
   - Aviso "o app não foi verificado": é esperado, pois o script é privado. Clique em **Avançado** e depois em **Acessar FotoLoop (não seguro)**. Isso só aparece porque você é o dono do script.
3. Ao terminar, abra **Execuções** (ou o log) e copie o endereço da pasta que aparece. Essa pasta se chama **FotoLoop - Lucia 60 anos** no seu Drive.

Confirme que a pasta **não** está compartilhada com ninguém: clique com o botão direito na pasta no Drive → **Compartilhar**. Deve aparecer somente você.

## 3. Publicar como aplicativo da web

1. Clique em **Implantar** → **Nova implantação**.
2. Tipo: **Aplicativo da Web**.
3. Descrição: `FotoLoop v1`.
4. **Executar como**: **Eu** (sua conta).
5. **Quem pode acessar**: **Qualquer pessoa**. Isso permite que os convidados enviem sem fazer login. Não é um acesso às suas fotos: o script só grava na pasta.
6. Clique em **Implantar**. Copie a **URL do aplicativo da Web**. Ela termina em `/exec`.

Se você alterar o `Code.gs` depois, use **Implantar → Gerenciar implantações → Editar → Nova versão**. A URL continua a mesma.

## 4. Ligar a página dos convidados

1. Abra [`web/convidados/config.js`](../web/convidados/config.js).
2. Cole a URL entre aspas:

   ```js
   window.FOTOLOOP_CONFIG = {
     endpoint: 'https://script.google.com/macros/s/SEU_CODIGO/exec'
   };
   ```

3. Publique a página (passo seguinte).

A URL não é uma senha, mas evite divulgá-la fora do evento. O script aceita apenas fotos (JPG, PNG, WebP, HEIC), verifica o tamanho (até 12 MB) e limita os envios por janela de 10 minutos.

## 5. Publicar a página dos convidados (GitHub Pages)

1. No GitHub, abra o repositório **bugijo/FotoLoop** → **Settings** → **Pages**.
2. Em **Source**, escolha **Deploy from a branch**, branch **main**, pasta **/ (root)**, e clique em **Save**.
3. Em alguns minutos a página fica em:
   `https://bugijo.github.io/FotoLoop/web/convidados/`
4. Teste essa página no celular antes da festa.

Assim que `config.js` estiver preenchido e publicado, a página envia as fotos ao Apps Script.

## 6. Testar a prova de funcionamento

Siga o checklist de [PROVA_FUNCIONAL.md](PROVA_FUNCIONAL.md), item "Fase 1".

## 7. Encerrar o recebimento depois da festa

Pelo painel do organizador (aba **Recebimento de fotos**). O painel grava o arquivo `_controle.json` na pasta do Drive. A página passa a mostrar que o envio foi encerrado. O Drive para computador sincroniza essa mudança em alguns minutos.

## Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| "Pasta não configurada" | Não rodou `configurarPastaDoEvento` | Rode a função no editor (passo 2) |
| "Não recebemos sua foto" | URL errada ou implantação antiga | Confira `config.js` e a URL `/exec` |
| "Muitos envios ao mesmo tempo" | Limite de 150 envios em 10 minutos | Aguarde um minuto; ajuste `ENVIOS_POR_JANELA` no `Code.gs` se necessário |
| Foto some do Drive | Está na lixeira | Recupere pela lixeira do Drive (a foto não é apagada pelo app) |
| Erro de permissão ao rodar | Autorização não concluída | Rode de novo e autorize com a conta do proprietário |
