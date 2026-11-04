(function () {
  'use strict';

  var CHAVE_SESSAO = 'fotoloop_senha';
  var INTERVALO_MS = 3000;
  var senha = '';
  var estado = null;
  var qrCarregado = false;

  function $(id) { return document.getElementById(id); }

  function mensagem(texto) {
    var caixa = $('mensagem');
    caixa.textContent = texto;
    caixa.hidden = !texto;
    if (texto) setTimeout(function () { if (caixa.textContent === texto) caixa.hidden = true; }, 4000);
  }

  // Todas as chamadas do painel levam a senha no cabeçalho; nada vai na URL.
  function api(caminho, corpo) {
    var opcoes = { method: corpo ? 'POST' : 'GET', headers: { 'X-Senha': senha } };
    if (corpo) {
      opcoes.headers['Content-Type'] = 'application/json';
      opcoes.body = JSON.stringify(corpo);
    }
    return fetch(caminho, opcoes).then(function (resposta) {
      return resposta.json().then(function (dados) {
        if (resposta.status === 401) {
          sair();
          throw new Error('Senha incorreta.');
        }
        if (!resposta.ok || dados.ok === false) {
          throw new Error(dados.mensagem || 'Não foi possível concluir.');
        }
        return dados;
      });
    });
  }

  function sair() {
    senha = '';
    sessionStorage.removeItem(CHAVE_SESSAO);
    $('conteudo').hidden = true;
    $('entrada').hidden = false;
  }

  function acao(dados) {
    return api('/api/painel/controle', dados).then(atualizar).catch(function (erro) {
      mensagem(erro.message);
    });
  }

  function atualizar() {
    return api('/api/painel').then(function (dados) {
      estado = dados;
      desenhar(dados);
    }).catch(function (erro) {
      if (estado === null) mensagem(erro.message);
    });
  }

  function desenhar(d) {
    var atual = d.atual ? 'Foto no telão: ' + d.atual.numero : 'Nenhuma foto no telão ainda';
    $('status-foto').textContent = atual + (d.pausada ? ' (pausada)' : '');
    $('status-fotos').textContent = 'Fotos prontas: ' + d.total + ' · pendentes: ' + d.pendentes + ' · rodada: ' + d.rodada;

    $('modo-auto').checked = !!d.modo_automatico;
    if (document.activeElement !== $('tempo-fixo')) {
      $('tempo-fixo').value = d.tempo_fixo_segundos;
    }

    $('texto-recebimento').textContent = d.recebendo
      ? 'Recebimento ABERTO: convidados podem enviar fotos.'
      : 'Recebimento ENCERRADO: a página dos convidados não aceita mais fotos.';

    var sinc = d.sincronizacao || {};
    var textoSinc = sinc.pasta_drive_encontrada
      ? 'Pasta do Google Drive encontrada. Última verificação: ' + (sinc.ultima_varredura || 'ainda não') + '.'
      : 'Pasta do Google Drive NÃO encontrada. Confira o Google Drive para computador.';
    if (sinc.erro) textoSinc += ' Aviso: ' + sinc.erro;
    $('texto-sincronizacao').textContent = textoSinc;

    $('texto-falhas').textContent = d.falhas.length
      ? 'Fotos que não puderam ser convertidas (fora do telão): ' +
        d.falhas.map(function (f) { return f.numero; }).join(', ') + '.'
      : 'Nenhuma falha de conversão.';

    $('contagem').textContent = d.recebidas;
    desenharGaleria(d.fotos);

    if (!qrCarregado && d.url_convidados) carregarQrCode();
  }

  function desenharGaleria(fotos) {
    var galeria = $('galeria');
    galeria.textContent = '';
    fotos.forEach(function (foto) {
      var cartao = document.createElement('div');
      cartao.className = 'foto' + (foto.oculta ? ' oculta' : '');

      if (foto.status === 'pronta') {
        var imagem = document.createElement('img');
        imagem.loading = 'lazy';
        imagem.alt = 'Foto ' + String(foto.numero).padStart(4, '0');
        imagem.src = foto.url;
        cartao.appendChild(imagem);
      } else {
        var aviso = document.createElement('p');
        aviso.className = 'falha';
        aviso.textContent = 'Não convertida';
        cartao.appendChild(aviso);
      }

      var legenda = document.createElement('div');
      legenda.textContent = String(foto.numero).padStart(4, '0') + (foto.oculta ? ' · oculta' : '');
      cartao.appendChild(legenda);

      if (foto.status === 'pronta') {
        var botao = document.createElement('button');
        botao.textContent = foto.oculta ? 'Mostrar' : 'Ocultar';
        botao.addEventListener('click', function () {
          acao({ acao: 'ocultar', numero: foto.numero, oculta: !foto.oculta });
        });
        cartao.appendChild(botao);
      }
      galeria.appendChild(cartao);
    });
  }

  function carregarQrCode() {
    qrCarregado = true;
    fetch('/api/painel/qrcode', { headers: { 'X-Senha': senha } })
      .then(function (resposta) {
        if (!resposta.ok) throw new Error('QR Code indisponível.');
        return resposta.blob();
      })
      .then(function (imagem) {
        var img = document.createElement('img');
        img.alt = 'QR Code da página dos convidados';
        img.src = URL.createObjectURL(imagem);
        $('qrcode').textContent = '';
        $('qrcode').appendChild(img);
      })
      .catch(function () { qrCarregado = false; });
  }

  function entrar(evento) {
    evento.preventDefault();
    senha = $('senha').value;
    $('erro-senha').hidden = true;
    api('/api/painel').then(function (dados) {
      sessionStorage.setItem(CHAVE_SESSAO, senha);
      $('entrada').hidden = true;
      $('conteudo').hidden = false;
      estado = dados;
      desenhar(dados);
      iniciarAtualizacao();
    }).catch(function (erro) {
      $('erro-senha').textContent = erro.message;
      $('erro-senha').hidden = false;
    });
  }

  var temporizador = null;
  function iniciarAtualizacao() {
    if (temporizador) return;
    temporizador = setInterval(atualizar, INTERVALO_MS);
  }

  function aoSalvarVelocidade() {
    var tempo = parseInt($('tempo-fixo').value, 10);
    acao({ acao: 'velocidade', modo_automatico: $('modo-auto').checked, tempo_fixo_segundos: tempo });
  }

  function aoAlternarRecebimento() {
    var aberto = !(estado && estado.recebendo);
    acao({ acao: 'recebimento', aberto: aberto }).then(function () {
      mensagem(aberto ? 'Recebimento aberto.' : 'Recebimento encerrado.');
    });
  }

  function aoAbrirBackup() {
    api('/api/painel/abrir-backup', {}).then(function (dados) {
      mensagem(dados.mensagem);
    }).catch(function (erro) { mensagem(erro.message); });
  }

  document.querySelectorAll('[data-acao]').forEach(function (botao) {
    botao.addEventListener('click', function () {
      acao({ acao: botao.getAttribute('data-acao') });
    });
  });
  $('formulario-senha').addEventListener('submit', entrar);
  $('salvar-velocidade').addEventListener('click', aoSalvarVelocidade);
  $('btn-recebimento').addEventListener('click', aoAlternarRecebimento);
  $('btn-backup').addEventListener('click', aoAbrirBackup);
  $('btn-imprimir').addEventListener('click', function () { window.print(); });

  var guardada = sessionStorage.getItem(CHAVE_SESSAO);
  if (guardada) {
    $('senha').value = guardada;
    entrar({ preventDefault: function () {} });
  }
})();
