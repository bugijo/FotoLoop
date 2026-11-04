@echo off
rem FotoLoop - inicia o telão no Windows 10/11. Dê dois cliques neste arquivo no notebook do evento.
chcp 65001 >nul
title FotoLoop - Telao
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale o Python 3.12 em python.org ^(marque "Add python.exe to PATH"^).
  pause
  exit /b 1
)

if not exist "config\fotoloop.json" (
  echo Falta o arquivo config\fotoloop.json.
  echo Rode instalar_windows.bat e preencha o arquivo. Veja docs\WINDOWS.md.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Preparando o FotoLoop pela primeira vez. Isso pode levar alguns minutos...
  py -m venv .venv
  if errorlevel 1 goto falha
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto falha
)

start "" http://127.0.0.1:8080/
.venv\Scripts\python.exe run.py
pause
exit /b 0

:falha
echo Nao foi possivel preparar o FotoLoop. Veja a mensagem acima.
pause
exit /b 1
