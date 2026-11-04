/**
 * FotoLoop — receptor de fotografias (Google Apps Script).
 *
 * Publicação: veja docs/CONFIGURAR_APPS_SCRIPT.md
 * Roda com as permissões da conta do proprietário; convidados não fazem login.
 * Nunca coloque senhas, tokens ou chaves neste arquivo.
 */

const FOTOLOOP = {
  TAMANHO_MAXIMO_BYTES: 12 * 1024 * 1024,
  ENVIOS_POR_JANELA: 150,
  JANELA_SEGUNDOS: 600,
  CHAVE_PASTA: 'PASTA_ID',
  NOME_CONTROLE: '_controle.json',
  NOME_PASTA_PADRAO: 'FotoLoop - Lucia 60 anos'
};

/**
 * Cria (ou reaproveita) a pasta privada do evento e guarda o identificador.
 * Execute esta função uma vez pelo editor do Apps Script.
 */
function configurarPastaDoEvento() {
  const propriedades = PropertiesService.getScriptProperties();
  const idExistente = propriedades.getProperty(FOTOLOOP.CHAVE_PASTA);
  const pasta = idExistente
    ? DriveApp.getFolderById(idExistente)
    : DriveApp.createFolder(FOTOLOOP.NOME_PASTA_PADRAO);
  propriedades.setProperty(FOTOLOOP.CHAVE_PASTA, pasta.getId());

  if (!pasta.getFilesByName(FOTOLOOP.NOME_CONTROLE).hasNext()) {
    pasta.createFile(FOTOLOOP.NOME_CONTROLE, JSON.stringify({ recebendo: true }), 'application/json');
  }
  console.log('Pasta do evento pronta: ' + pasta.getUrl());
  return pasta.getUrl();
}

/** Consulta de status (GET ?acao=status). Também usada pela página dos convidados. */
function doGet(e) {
  try {
    const acao = (e && e.parameter && e.parameter.acao) || 'status';
    if (acao !== 'status') {
      return resposta_(falha_('acao_desconhecida', 'Pedido não reconhecido.'));
    }
    const pasta = pastaDoEvento_();
    return resposta_({ ok: true, recebendo: recebendoFotos_(pasta) });
  } catch (erro) {
    console.error(erro);
    return resposta_(falha_('erro_interno', 'Serviço indisponível no momento.'));
  }
}

/** Recebe uma fotografia (POST, corpo JSON enviado como text/plain). */
function doPost(e) {
  try {
    const pedido = JSON.parse(e.postData.contents);
    return resposta_(receberFoto_(pedido));
  } catch (erro) {
    console.error(erro);
    return resposta_(falha_('pedido_invalido', 'Não recebemos sua foto. Tente de novo.'));
  }
}

function receberFoto_(pedido) {
  const pasta = pastaDoEvento_();

  if (!recebendoFotos_(pasta)) {
    return falha_('recebimento_encerrado', 'O envio de fotos já foi encerrado. Obrigada por participar!');
  }
  if (!dentroDoLimite_()) {
    return falha_('limite_temporario', 'Muitos envios ao mesmo tempo. Aguarde um minuto e tente de novo.');
  }
  if (!pedido || typeof pedido.dados !== 'string' || pedido.dados.length === 0) {
    return falha_('pedido_invalido', 'Não recebemos sua foto. Tente de novo.');
  }

  const bytes = Utilities.base64Decode(pedido.dados);
  if (bytes.length === 0) {
    return falha_('arquivo_vazio', 'Essa foto está vazia. Escolha outra.');
  }
  if (bytes.length > FOTOLOOP.TAMANHO_MAXIMO_BYTES) {
    return falha_('arquivo_grande', 'Essa foto é muito grande. Escolha outra, por favor.');
  }
  const tipo = detectarTipo_(bytes);
  if (!tipo) {
    return falha_('formato_invalido', 'Esse arquivo não é uma foto compatível. Use JPG, PNG, WebP ou HEIC.');
  }

  // O nome é derivado do conteúdo: a mesma foto enviada duas vezes não gera cópia.
  const sha256 = hexSha256_(bytes);
  const identificador = 'FL_' + sha256.substring(0, 16);
  const nomeArquivo = identificador + '.' + tipo.extensao;
  const nomeOriginal = nomeSeguro_(pedido.nome);

  const trava = LockService.getScriptLock();
  trava.waitLock(25000);
  try {
    if (pasta.getFilesByName(nomeArquivo).hasNext()) {
      const arquivoExistente = pasta.getFilesByName(nomeArquivo).next();
      garantirMetadados_(pasta, identificador, {
        identificador: identificador,
        nome_original: nomeOriginal,
        tipo: tipo.mime,
        tamanho_bytes: bytes.length,
        sha256: sha256,
        enviado_em: new Date().toISOString(),
        id_drive: arquivoExistente.getId()
      });
      return { ok: true, duplicada: true, identificador: identificador, mensagem: 'Esta foto já estava no álbum. Obrigada!' };
    }

    const arquivo = pasta.createFile(Utilities.newBlob(bytes, tipo.mime, nomeArquivo));
    const metadados = {
      identificador: identificador,
      nome_original: nomeOriginal,
      tipo: tipo.mime,
      tamanho_bytes: bytes.length,
      sha256: sha256,
      enviado_em: new Date().toISOString(),
      id_drive: arquivo.getId()
    };
    garantirMetadados_(pasta, identificador, metadados);
    return { ok: true, duplicada: false, identificador: identificador, mensagem: 'Foto recebida!' };
  } finally {
    trava.releaseLock();
  }
}

function pastaDoEvento_() {
  const id = PropertiesService.getScriptProperties().getProperty(FOTOLOOP.CHAVE_PASTA);
  if (!id) {
    throw new Error('Pasta não configurada. Execute configurarPastaDoEvento().');
  }
  return DriveApp.getFolderById(id);
}

/** Lê _controle.json (alterado pelo painel do notebook). Ausente ou ilegível = aberto. */
function recebendoFotos_(pasta) {
  const arquivos = pasta.getFilesByName(FOTOLOOP.NOME_CONTROLE);
  if (!arquivos.hasNext()) {
    return true;
  }
  try {
    return JSON.parse(arquivos.next().getBlob().getDataAsString()).recebendo !== false;
  } catch (erro) {
    return true;
  }
}

function garantirMetadados_(pasta, identificador, metadados) {
  const nomeJson = identificador + '.json';
  if (!pasta.getFilesByName(nomeJson).hasNext()) {
    pasta.createFile(nomeJson, JSON.stringify(metadados, null, 2), 'application/json');
  }
}

/** Limite global simples por janela de tempo (evita abuso e picos acidentais). */
function dentroDoLimite_() {
  const cache = CacheService.getScriptCache();
  const janela = Math.floor(Date.now() / (FOTOLOOP.JANELA_SEGUNDOS * 1000));
  const chave = 'envios_' + janela;
  const usados = parseInt(cache.get(chave) || '0', 10);
  if (usados >= FOTOLOOP.ENVIOS_POR_JANELA) {
    return false;
  }
  cache.put(chave, String(usados + 1), FOTOLOOP.JANELA_SEGUNDOS + 60);
  return true;
}

/** Confere a assinatura do arquivo (não confia na extensão nem no tipo enviado). */
function detectarTipo_(bytes) {
  if (bytes.length < 12) {
    return null;
  }
  const at = function (i) { return bytes[i] & 0xFF; };
  if (at(0) === 0xFF && at(1) === 0xD8 && at(2) === 0xFF) {
    return { extensao: 'jpg', mime: 'image/jpeg' };
  }
  if (at(0) === 0x89 && at(1) === 0x50 && at(2) === 0x4E && at(3) === 0x47) {
    return { extensao: 'png', mime: 'image/png' };
  }
  if (texto_(bytes, 0, 4) === 'RIFF' && texto_(bytes, 8, 4) === 'WEBP') {
    return { extensao: 'webp', mime: 'image/webp' };
  }
  if (texto_(bytes, 4, 4) === 'ftyp') {
    const marca = texto_(bytes, 8, 4);
    if (['heic', 'heix', 'hevc', 'heim', 'heis', 'mif1', 'msf1'].indexOf(marca) !== -1) {
      return { extensao: 'heic', mime: 'image/heic' };
    }
  }
  return null;
}

function texto_(bytes, inicio, tamanho) {
  let saida = '';
  for (let i = inicio; i < inicio + tamanho; i++) {
    saida += String.fromCharCode(bytes[i] & 0xFF);
  }
  return saida;
}

function hexSha256_(bytes) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, bytes)
    .map(function (b) { return ((b & 0xFF) + 0x100).toString(16).slice(1); })
    .join('');
}

function nomeSeguro_(nome) {
  const texto = String(nome || 'foto')
    .split(/[\\/]/).pop()
    .replace(/[\u0000-\u001f]/g, '')
    .trim();
  return (texto || 'foto').substring(0, 120);
}

function falha_(codigo, mensagem) {
  return { ok: false, codigo: codigo, mensagem: mensagem };
}

function resposta_(objeto) {
  return ContentService.createTextOutput(JSON.stringify(objeto))
    .setMimeType(ContentService.MimeType.JSON);
}
