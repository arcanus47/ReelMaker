# REELMAKER 0.6.0 — AI Video Studio

Aplicación de escritorio para convertir vídeos largos y transmisiones en clips cortos mediante transcripción local, análisis de momentos y procesamiento con FFmpeg.

> **Estado:** versión de desarrollo. Antes de distribuir binarios, compila y prueba la aplicación en el sistema operativo de destino.

## Características

- Importación y gestión de vídeos con proyectos persistentes en SQLite.
- Transcripción local con `faster-whisper`.
- Detección heurística de momentos candidatos a partir de la transcripción.
- Edición de títulos y tiempos de los clips.
- Exportación MP4 mediante FFmpeg.
- Subtítulos SRT generados desde la transcripción e incrustados en el vídeo.
- Captura de directos por segmentos y análisis incremental con Live Clipping.
- Formatos de salida vertical, horizontal y cuadrado.
- Interfaz renovada **Midnight Studio**, con paleta oscura fría y logo en el menú lateral.
- Modelos, proyectos, exportaciones y datos de usuario guardados fuera del código fuente.

## Capturas

Añade aquí capturas de pantalla de la aplicación para mostrar la interfaz en GitHub.

## Requisitos

- Python 3.12 recomendado.
- FFmpeg y FFprobe disponibles en `PATH`.
- Conexión a Internet para instalar dependencias y descargar por primera vez el modelo Whisper.
- Para el procesamiento de vídeo y modelos de IA, se recomienda disponer de memoria RAM suficiente y espacio libre para los archivos temporales.

## Ejecutar desde el código fuente

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg libass9 \
  libxcb-cursor0 libxkbcommon-x11-0 libegl1 libgl1 libglib2.0-0 libdbus-1-3

git clone <URL_DEL_REPOSITORIO>
cd REELMAKER

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m app.main
```

### Windows

1. Instala Python 3.12 de 64 bits.
2. Instala FFmpeg y FFprobe, o coloca `ffmpeg.exe` y `ffprobe.exe` en `app/tools/ffmpeg/bin/`.
3. Abre CMD en la carpeta del proyecto.
4. Ejecuta:

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m app.main
```

## Construir una versión portable

### Ubuntu

El repositorio incluye `REELMAKER_ubuntu.spec` y `build_ubuntu.sh`. El script instala dependencias del sistema mediante `sudo apt`, crea un entorno de compilación separado y genera una carpeta portable:

```bash
chmod +x build_ubuntu.sh
./build_ubuntu.sh
```

El resultado esperado es:

```text
dist/REELMAKER_UBUNTU/
dist/REELMAKER_0.6.0_UBUNTU_x86_64.tar.gz
```

### Windows

Consulta [`BUILD_WINDOWS.md`](BUILD_WINDOWS.md). El workflow de GitHub Actions también permite construir el paquete Windows desde **Actions → Build REELMAKER for Windows → Run workflow**.

## Pruebas

Con las dependencias instaladas y FFmpeg disponible:

```bash
python -m compileall -q app tests
python -m unittest discover -s tests -v
```

La prueba de integración requiere FFmpeg con soporte para H.264 (`libx264`) y subtítulos (`libass`).

## Datos y privacidad

REELMAKER procesa los archivos localmente. Los modelos Whisper se descargan en el primer uso. La aplicación guarda datos de trabajo en una carpeta de usuario (`~/.reelmaker` en Linux y `%LOCALAPPDATA%\\REELMAKER` en Windows cuando está empaquetada). No subas vídeos, modelos, bases de datos, credenciales, cookies ni archivos de configuración privados al repositorio.

## Limitaciones conocidas

- La selección de momentos se basa en heurísticas sobre la transcripción; no garantiza viralidad ni sustituye la revisión humana.
- El encuadre vertical utiliza recorte centrado; no implica seguimiento automático de rostros.
- Los clips de Live Clipping se analizan por segmentos y no necesariamente combinan frases que atraviesen el límite entre segmentos.
- La disponibilidad de directos depende de la plataforma, la sesión, las cookies y las restricciones del contenido. No se garantiza acceso a transmisiones privadas, DRM o contenido de pago.
- El rendimiento depende del procesador, la memoria, el modelo Whisper y la duración del material.

Utiliza REELMAKER únicamente con contenido que tengas derecho a procesar.

## Estructura principal

```text
app/
  core/       Gestión y procesamiento de vídeo
  database/   Persistencia SQLite
  ui/         Interfaz, tema e iconos
  workers/    Tareas de análisis y captura
  assets/     Recursos visuales
tests/        Pruebas automatizadas
```

## Contribuciones

Los cambios deben mantener separadas la interfaz, la lógica de procesamiento, la persistencia y las tareas en segundo plano. Ejecuta las pruebas antes de enviar un pull request.

## Licencia

No se ha incluido una licencia en esta versión. Añade un archivo `LICENSE` antes de publicar el repositorio si deseas conceder permisos explícitos de uso, modificación y redistribución.
