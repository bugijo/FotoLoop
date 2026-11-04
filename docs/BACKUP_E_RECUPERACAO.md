# Backup e recuperação

O FotoLoop mantém **três** camadas de proteção. A pasta do Drive **não** é tratada como backup independente, porque uma exclusão ou alteração acidental na nuvem se propaga para ela.

| Camada | Onde fica | O que protege |
|---|---|---|
| 1. Google Drive (nuvem) | Pasta privada do proprietário | Perda do notebook |
| 2. Pasta do Drive no notebook | `pasta_drive` (sincronizada) | Queda da internet |
| 3. Cópia de segurança | `pasta_backup` (fora do Drive) | Exclusão ou alteração na nuvem, e queda do Drive |

## O que existe na cópia de segurança

```
backup/
├── fotoloop.db              # registro: número ↔ nome original ↔ id do Drive ↔ status
├── originais/
│   ├── 0001_FL_xxxx.jpg     # foto original, sem alterações
│   ├── 0001_FL_xxxx.json    # metadados enviados (nome original, horário, id do Drive)
│   └── ...
└── projetor/
    ├── 0001.jpg             # JPEG usado no telão (orientação corrigida)
    └── ...
```

- Os originais são copiados e **verificados por hash** (SHA-256). Se a cópia não confere, o arquivo não é aceito.
- O banco `fotoloop.db` guarda o número definitivo de cada foto e a fila da apresentação.
- Os JPEGs do projetor podem ser refeitos a partir dos originais a qualquer momento.

## Backup extra (recomendado após a festa)

1. Copie a pasta `backup` inteira para um pendrive ou HD externo.
2. Faça uma segunda cópia em outro local (outro computador ou outra conta de nuvem).
3. Ao copiar com o telão aberto, feche o programa antes (`Ctrl+C` no terminal) para o banco não ficar no meio de uma gravação.

## Recuperação

### A. O notebook pegou fogo, quebrou ou foi trocado

1. Instale o FotoLoop no novo notebook (`WINDOWS.md`).
2. Copie a pasta `backup` de volta para o mesmo caminho definido em `pasta_backup`.
3. Inicie o telão. Ele reconhece o banco e continua a numeração de onde parou.
4. As fotos que ainda estão na nuvem e não estão na cópia são sincronizadas pelo Drive e numeradas na sequência.

### B. Foto apagada do telão por engano

- Pelo painel, use **Mostrar** na foto oculta. Se a foto não aparecer, o original está em `backup\originais`.
- Ocultar não apaga nada. Para refazer o JPEG, apague `backup\projetor\NNNN.jpg` e reinicie o telão: ele gera de novo a partir do original.

### C. Foto apagada do Google Drive

- Procure na lixeira do Drive (30 dias). Se já passou, a cópia em `backup\originais` continua disponível.

### D. Reinício do notebook durante a festa

- Nada se perde. Ao iniciar `iniciar_telao.bat`, a apresentação retoma a foto e a posição salvas.

### E. Banco de dados corrompido

- Renomeie `fotoloop.db` (e os arquivos `fotoloop.db-wal` e `fotoloop.db-shm`) para `.antigo`.
- Reinicie. O FotoLoop reconstrói a lista a partir de `backup\originais` na próxima varredura. A ordem de números pode mudar; por isso mantenha uma cópia do banco antes de qualquer manutenção.

## Observação sobre privacidade

A pasta `backup` contém as fotos originais dos convidados. Trate-a como dado pessoal: não a envie para repositórios públicos nem compartilhe com terceiros.
