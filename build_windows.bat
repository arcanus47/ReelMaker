@echo off
setlocal
cd /d "%~dp0"
title REELMAKER - Windows Build

echo ==========================================
echo       REELMAKER 0.3.1 - BUILD
echo ==========================================

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Instala Python 3.12 x64 y activa Add Python to PATH.
  pause
  exit /b 1
)

if not exist "tools\ffmpeg\bin\ffmpeg.exe" (
  echo ERROR: Falta tools\ffmpeg\bin\ffmpeg.exe
  echo Consulta BUILD_WINDOWS.md.
  pause
  exit /b 1
)
if not exist "tools\ffmpeg\bin\ffprobe.exe" (
  echo ERROR: Falta tools\ffmpeg\bin\ffprobe.exe
  pause
  exit /b 1
)

if not exist ".venv" py -3.12 -m venv .venv
call .venv\Scripts\activate.bat
if errorlevel 1 goto error

python -m pip install --upgrade pip
if errorlevel 1 goto error
python -m pip install -r requirements-build.txt
if errorlevel 1 goto error

set "PATH=%CD%\tools\ffmpeg\bin;%PATH%"
python -m compileall -q app tests
if errorlevel 1 goto error
python -m unittest discover -s tests -v
if errorlevel 1 goto error

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist REELMAKER.spec del /q REELMAKER.spec

pyinstaller --noconfirm --clean --windowed --onedir --name REELMAKER ^
  --collect-all PySide6 ^
  --collect-all faster_whisper ^
  --collect-all ctranslate2 ^
  --collect-all av ^
  --collect-all tokenizers ^
  --collect-all huggingface_hub ^
  --add-binary "tools\ffmpeg\bin\ffmpeg.exe;ffmpeg\bin" ^
  --add-binary "tools\ffmpeg\bin\ffprobe.exe;ffmpeg\bin" ^
  app\main.py
if errorlevel 1 goto error

if not exist "dist\REELMAKER\REELMAKER.exe" goto error

rem FFmpeg shared builds may require DLL files beside ffmpeg.exe/ffprobe.exe.
if not exist "dist\REELMAKER\_internal\ffmpeg\bin" mkdir "dist\REELMAKER\_internal\ffmpeg\bin"
copy /y "tools\ffmpeg\bin\*.dll" "dist\REELMAKER\_internal\ffmpeg\bin\" >nul 2>nul

echo.
echo BUILD OK: dist\REELMAKER\REELMAKER.exe
echo IMPORTANTE: distribuye la carpeta dist\REELMAKER completa.
pause
exit /b 0

:error
echo.
echo BUILD FALLIDO. Revisa el error mostrado arriba.
pause
exit /b 1
