# FotoLoop

Telão de fotos ao vivo para festas. Os convidados escaneiam um QR Code, enviam uma foto pelo celular e ela aparece automaticamente no projetor.

Projeto da festa de **60 anos da Lúcia (07/11/2026)**. Feito para ser gratuito: Google Apps Script, Google Drive pessoal e um notebook com Windows.

## Como funciona

```
Celular do convidado ──► Página servida pelo Google Apps Script ──► google.script.run ──► Google Drive (pasta privada)
                                                                                    │
                                                  Google Drive para computador (notebook Windows)
                                                                                    │
                          Cópia de segurança independente ◄── FotoLoop (Python) ──► Telão no projetor
```

- **Convidados**: abrem a página, tiram ou escolhem uma foto, confirmam. Não precisam instalar nada nem fazer login.
- **Drive**: as fotos entram numa pasta privada do proprietário. Convidados não veem nem apagam nada.
- **Notebook**: copia cada foto para uma pasta de backup separada, numera (0001, 0002...), gera JPEG para o projetor e mostra o telão em tela cheia (layout 4 + 1 + 4).
- **Painel do organizador**: protegido por senha. Pausa, avança, muda a velocidade, oculta fotos, abre ou encerra o recebimento e imprime o QR Code.

## Estrutura

| Pasta / arquivo | Conteúdo |
|---|---|
| `apps_script/` | Página dos convidados e recebimento das fotos (Google Apps Script): `Code.gs`, `Convidados.html`, `Estilo.html`, `Script.html`, `appsscript.json` |
| `web/convidados/` | Redirecionamento no GitHub Pages para a página do Apps Script |
| `web/telao/` | Telão (projetor) |
| `web/painel/` | Painel do organizador |
| `fotoloop/` | Núcleo em Python: fila, velocidade, numeração, conversão, sincronização e servidor |
| `tests/` | Testes automatizados (`python -m unittest discover -s tests -t .`) |
| `config/fotoloop.exemplo.json` | Modelo de configuração, **sem senhas** |
| `run.py` | Inicia o telão |
| `iniciar_telao.bat`, `instalar_windows.bat` | Atalhos para Windows |
| `docs/` | Guias de configuração, Windows, projetor, backup e QR Code |

## Guias

1. [Configurar o Google Apps Script e o Drive](docs/CONFIGURAR_APPS_SCRIPT.md)
2. [Instalação e uso no Windows, incluindo o projetor](docs/WINDOWS.md)
3. [Backup e recuperação](docs/BACKUP_E_RECUPERACAO.md)
4. [QR Code definitivo](docs/QR_CODE.md)
5. [Prova de funcionamento (checklist)](docs/PROVA_FUNCIONAL.md)

## Ordem de números e prioridade

- Cada foto recebe um número definitivo. Ele nunca muda, mesmo após reinício.
- Fotos novas aparecem primeiro, em ordem de chegada. Depois a apresentação volta de onde parou.
- Para que uma sequência contínua de fotos novas não bloqueie as antigas, a cada 30 novas seguidas são exibidas 2 antigas.
- Velocidade automática: até 10 fotos pendentes → 10 s; 11 a 14 → 8 s; 15 a 49 → 5 s; 50 ou mais → 3 s. Também é possível fixar um tempo.

## Testes

```bash
python -m unittest discover -s tests -t .
```

Os testes cobrem fila, velocidade, numeração, persistência, orientação EXIF, HEIC, arquivos inválidos, sincronização sem repetição, reconexão e a proteção do painel. Testes com celulares, login do Google e projetor real são manuais (veja `docs/PROVA_FUNCIONAL.md`).

## Segurança e privacidade

- O repositório é **público**. Nunca commitar `config/fotoloop.json`, `backup/`, fotos ou senhas. O `.gitignore` já impede isso.
- O painel exige senha. Por padrão só aceita conexões do próprio notebook.
- Fotos enviadas são validadas pela assinatura do arquivo, pelo tamanho e pelo limite de envios por janela de tempo.
- A página e o telão avisam que as fotos serão exibidas e guardadas para o álbum.

## Limites conhecidos

- O envio depende de internet no celular do convidado. Sem conexão a foto não sai do aparelho; a página informa e permite tentar de novo.
- A página de envio não impede totalmente abuso por alguém que conheça a URL do Apps Script. O limite global e o botão de encerrar recebimento reduzem o risco.
- Fotos muito grandes (acima de 12 MB) são recusadas pelo receptor.
- Integrações futuras (WhatsApp, Instagram, fotógrafos) não fazem parte desta versão.

## Licença

Uso privado para o evento. Defina a licença antes de torná-lo um produto reutilizável.
