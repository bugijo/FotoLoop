# Configurar o Google Apps Script e o Google Drive

Esta etapa é feita **uma vez**, com a conta Google do proprietário (a mesma do Google Drive onde as fotos ficam). Não custa nada.

## Arquitetura definitiva

- A **página dos convidados** é servida pelo próprio Apps Script (`HtmlService`), a partir de `Convidados.html`.
- As fotos são enviadas com **`google.script.run`**, a chamada interna do Apps Script. Não há requisição entre domínios, por isso não há bloqueio de CORS.
- O servidor só responde "recebida" depois de confirmar no Drive que o arquivo existe e tem o tamanho enviado. Sem essa confirmação, a página mostra erro.
- O endereço do GitHub Pages (`https://bugijo.github.io/FotoLoop/web/convidados/`) é só uma página de redirecionamento para o endereço do Apps Script.

## 1. Criar o projeto de script

1. Abra <https://script.google.com> com a conta Google do proprietário.
2. Clique em **Novo projeto** e renomeie para `FotoLoop`.
3. No editor, use o botão **+** ao lado de *Arquivos* e crie **três** arquivos. Os nomes devem ser exatamente estes:

   | Arquivo no editor | Tipo | Conteúdo (copie de `apps_script/`) |
   |---|---|---|
   | `Code` (já existe; é o `Código.gs`) | Script | `Code.gs` |
   | `Convidados` | HTML | `Convidados.html` |
   | `Estilo` | HTML | `Estilo.html` |
   | `Script` | HTML | `Script.html` |

   Para cada arquivo: **selecione todo o conteúdo que já estiver no editor e substitua pelo conteúdo do arquivo do repositório**, sem remover nem acrescentar nada. Os arquivos `Estilo.html` e `Script.html` já trazem as próprias tags `<style>` e `<script>`, e elas devem ficar exatamente como estão no repositório. Não envolva esses arquivos em outra tag.

   Ao criar `Convidados`, `Estilo` e `Script` como HTML, o Apps Script acrescenta `.html` sozinho. O `Code.gs` precisa conter a função `include`, que insere `Estilo` e `Script` dentro de `Convidados`. Ela já está em `Code.gs`.

4. Abra **Configurações do projeto** (engrenagem) e marque **Mostrar o arquivo de manifesto appsscript.json**. Volte a **Editor**, abra `appsscript.json` e substitua o conteúdo pelo de `apps_script/appsscript.json`. Salve (Ctrl+S).

## 2. Criar a pasta privada no Drive

1. No menu de funções, escolha **configurarPastaDoEvento** e clique em **Executar**.
2. Na primeira vez o Google pede autorização: **Revisar permissões** → sua conta → **Avançado** → **Acessar FotoLoop (não seguro)** → **Permitir**. O aviso aparece porque o script é privado e só você o usa.
3. Veja no **Registro de execução** o endereço da pasta. Ela se chama **FotoLoop - Lucia 60 anos** no seu Drive.
4. Confirme que a pasta não está compartilhada: no Drive, clique com o botão direito → **Compartilhar**. Só você deve aparecer.

## 3. Publicar como aplicativo da web

1. **Implantar** → **Nova implantação**.
2. Tipo: **Aplicativo da Web**.
3. **Executar como**: **Eu**.
4. **Quem pode acessar**: **Qualquer pessoa**. Os convidados não precisam de login. Isso não dá acesso às suas fotos: o script só grava na pasta.
5. **Implantar** e copie a **URL do aplicativo da Web** (termina em `/exec`).

Depois de alterar o código: **Implantar → Gerenciar implantações → Editar → Nova versão → Implantar**. A URL continua a mesma.

## 4. Testar a página antes de divulgar

1. Abra a URL `/exec` no navegador do computador. Deve aparecer a página "60 anos de LÚCIA".
2. Abra `URL/exec?acao=status` (com `?acao=status` no fim). Deve aparecer `{"ok":true,"recebendo":true}`.
3. No celular, abra a URL `/exec` e envie uma foto de teste.

## 5. Ligar o endereço no GitHub Pages (redirecionamento)

1. Abra [`web/convidados/config.js`](../web/convidados/config.js) e cole a URL em `paginaApps`:

   ```js
   window.FOTOLOOP_CONFIG = {
     paginaApps: 'https://script.google.com/macros/s/SEU_CODIGO/exec'
   };
   ```

2. Salve, faça commit e push. O GitHub Pages atualiza sozinho.
3. Guarde a URL `/exec` para o QR Code e para `url_convidados` no `config/fotoloop.json` do notebook.

## Limites do Apps Script para este projeto

Consultados em 04/11/2026 na página oficial de quotas do Google:

| Limite | Valor | Impacto |
|---|---|---|
| Tempo de execução por chamada | 6 minutos | Sobra folga para uma foto de 12 MB |
| Execuções simultâneas por usuário | 30 | Os envios rodam como você (dono do script). Mais de 30 ao mesmo tempo viram erro e a página pede para tentar de novo |
| Execuções simultâneas por script | 1.000 | Não é o gargalo |
| Envios por janela de 10 minutos | 150 (definido no `Code.gs`) | Proteção contra abuso; ajuste em `ENVIOS_POR_JANELA` se necessário |

Limites **não documentados** oficialmente, e por isso a primeira foto real precisa testá-los:

- **Tamanho máximo do argumento de `google.script.run`.** A foto vai em base64, cerca de 33% maior que o arquivo. O limite do app é 12 MB de arquivo (`TAMANHO_MAXIMO_BYTES`). Se uma foto de 10 a 12 MB falhar, reduza esse valor para 8 MB e avise: a solução é enviar em partes.
- **Cota de criação de arquivos no Drive.** Não aparece na página de quotas. Na conta com 369 GB livres, o armazenamento não é o problema.

Fotos de iPhone (HEIC) costumam ter 2 a 4 MB; cabem com folga. Elas são guardadas como chegaram. A conversão para o telão é feita no notebook.

## 6. Encerrar o recebimento depois da festa

Pelo painel do organizador (aba **Recebimento de fotos**). O painel grava `_controle.json` na pasta do Drive; o Apps Script lê esse arquivo e passa a recusar fotos. O Drive para computador leva alguns minutos para sincronizar essa mudança.

## Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Página em branco ou "Pasta não configurada" | Não rodou `configurarPastaDoEvento` | Rode a função (passo 2) |
| "Não conseguimos confirmar que sua foto foi salva" | O arquivo não chegou ao Drive | Confira o Registro de execução do Apps Script e tente de novo |
| Erro ao enviar foto grande | Limite de `google.script.run` (ver acima) | Reduza `TAMANHO_MAXIMO_BYTES` e avise |
| "Muitos envios ao mesmo tempo" | Limite de 150 por 10 minutos | Aguarde um minuto |
| Foto some do Drive | Está na lixeira | Recupere pela lixeira (o app não apaga fotos) |
