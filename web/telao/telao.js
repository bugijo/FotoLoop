(function () {
  'use strict';

  var INTERVALO_CONSULTA_MS = 1000;
  var ultimaUrl = null;

  function $(id) { return document.getElementById(id); }

  function miniatura(foto, classe) {
    var caixa = document.createElement('div');
    caixa.className = 'mini ' + classe;
    var imagem = new Image();
    imagem.alt = 'Foto ' + foto.numero;
    imagem.src = foto.url;
    caixa.appendChild(imagem);
    var numero = document.createElement('span');
    numero.textContent = foto.numero;
    caixa.appendChild(numero);
    return caixa;
  }

  function preencherLateral(id, fotos, classe) {
    var lateral = $(id);
    lateral.textContent = '';
    fotos.forEach(function (foto) {
      lateral.appendChild(miniatura(foto, classe));
    });
  }

  function trocarFoto(url) {
    if (url === ultimaUrl) return;
    ultimaUrl = url;
    var principal = $('principal');
    var pre = new Image();
    pre.onload = function () {
      principal.classList.add('oculta');
      setTimeout(function () {
        principal.src = url;
        principal.classList.remove('oculta');
      }, 500);
    };
    // Foto ilegível: o servidor já a deixa de fora; aqui apenas não trava a tela.
    pre.onerror = function () { ultimaUrl = null; };
    pre.src = url;
  }

  function mostrar(estado) {
    preencherLateral('anteriores', estado.anteriores, 'antiga');
    preencherLateral('proximas', estado.proximas, 'proxima');

    if (estado.atual) {
      $('vazio').style.display = 'none';
      trocarFoto(estado.atual.url);
    } else {
      $('vazio').style.display = '';
      $('principal').removeAttribute('src');
      ultimaUrl = null;
    }
  }

  function consultar() {
    var pedido = fetch('/api/apresentacao', { cache: 'no-store' })
      .then(function (resposta) { return resposta.json(); })
      .then(mostrar)
      .catch(function () { /* sem conexão com o computador: tenta de novo sem avisar o público */ });
    pedido.then(function () { setTimeout(consultar, INTERVALO_CONSULTA_MS); });
  }

  consultar();
})();
