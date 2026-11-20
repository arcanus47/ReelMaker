# Construir REELMAKER.exe en Windows

## Tipo de distribución
Se genera una carpeta portable **one-folder** con `dist/REELMAKER/REELMAKER.exe` y todas sus bibliotecas. No se debe copiar únicamente el EXE.

## Requisitos
- Windows 10/11 de 64 bits.
- Python 3.12 de 64 bits.
- Internet durante la instalación de dependencias.
- FFmpeg para Windows, con soporte de H.264 (libx264) y subtítulos (libass).

## Preparar FFmpeg
Coloca estos dos ejecutables en `tools/ffmpeg/bin/`:

```text
tools/
  ffmpeg/
    bin/
      ffmpeg.exe
      ffprobe.exe
```

Verifica desde CMD que ambos funcionan:
`tools\\ffmpeg\\bin\\ffmpeg.exe -version`
`tools\\ffmpeg\\bin\\ffprobe.exe -version`

## Construir
Ejecuta `build_windows.bat`. El script crea `.venv`, instala requirements, compila la sintaxis y ejecuta PyInstaller.

Resultado: `dist/REELMAKER/REELMAKER.exe`.

## Datos y modelos
La base de datos, proyectos, exportaciones, temporales y modelos se guardan en `%LOCALAPPDATA%\\REELMAKER`. El modelo Whisper se descarga la primera vez que se utiliza; esa descarga inicial requiere internet.

## Limpieza
No se incluyen la base de datos de desarrollo, vídeos, exportaciones, modelos descargados, entornos virtuales ni carpetas `build/` o `dist/`.

## Nota de validación
El paquete puede validarse estáticamente en Linux, pero el EXE debe construirse y probarse en Windows. Esta carpeta incluye pruebas automáticas para DB y FFmpeg; ejecútalas en el entorno de desarrollo antes de distribuir.

## Pruebas antes de distribuir
En el entorno de desarrollo ejecuta `python -m unittest discover -s tests -v`.
La prueba de integración genera un vídeo de prueba, lo inspecciona, incrusta subtítulos y exporta un MP4.
La interfaz PySide6 debe abrirse y probarse manualmente en Windows después de construir el paquete.

## Alternativa si desarrollas desde Ubuntu
El repositorio incluye `.github/workflows/build-windows.yml`. Sube el proyecto a un repositorio GitHub, abre **Actions → Build REELMAKER for Windows → Run workflow**. GitHub construirá la carpeta Windows y publicará el artefacto `REELMAKER-Windows-x64` para descargar. El workflow descarga FFmpeg durante el build y ejecuta las pruebas antes de empaquetar.
