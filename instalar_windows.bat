@echo off
rem FotoLoop - prepara o arquivo de configuração no Windows (executar uma vez).
chcp 65001 >nul
title FotoLoop - Instalacao
cd /d "%~dp0"

if not exist "config\fotoloop.json" (
  copy "config\fotoloop.exemplo.json" "config\fotoloop.json" >nul
  echo Arquivo config\fotoloop.json criado.
) else (
  echo config\fotoloop.json ja existe; nada foi alterado.
)

echo.
echo Abra config\fotoloop.json no Bloco de Notas e preencha:
echo   - pasta_drive: a pasta do Google Drive que o Google Drive para computador sincroniza
echo   - senha_painel: uma senha sua para o painel do organizador
echo   - url_convidados: o endereco da pagina dos convidados
echo.
notepad "config\fotoloop.json"
pause
