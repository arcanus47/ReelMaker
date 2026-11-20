# REELMAKER 0.3.1

Aplicación de escritorio local para convertir vídeos largos en clips verticales.

## Funciones implementadas
- Importación e inspección de vídeos mediante FFprobe.
- Gestión y persistencia de proyectos en SQLite.
- Transcripción local con faster-whisper en CPU / int8.
- Generación de ventanas candidatas a partir de la transcripción (heurística inicial, no un modelo semántico).
- Edición manual del título y tiempos de cada clip.
- Exportación MP4 H.264/AAC en 1080x1920 mediante FFmpeg.
- Subtítulos SRT generados desde la transcripción y quemados en el vídeo exportado.
- Panel de exportaciones y apertura de la carpeta de salida.

## Requisitos (Ubuntu 24.04)
```bash
sudo apt update
sudo apt install -y ffmpeg python3 python3-pip python3-venv python3-dev libass9
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m app.main
```

## Flujo
1. Dashboard → Importar vídeo.
2. Proyectos → selecciona el proyecto.
3. Análisis IA → Analizar proyecto seleccionado. En la primera ejecución Whisper descargará el modelo elegido.
4. Editor de clips → revisa y modifica título, inicio y fin; pulsa Guardar cambios.
5. Exportar clip seleccionado o Exportar todos.
6. Los MP4 aparecen en `exports/`.

## Rendimiento
Configuración inicial recomendada para Intel Core i3 de doble núcleo y 16 GB RAM: Whisper `base`, CPU, int8, 2 hilos. `tiny` es más rápido y `small` puede ser más preciso pero lento. El primer uso requiere internet para descargar el modelo; una vez descargado, la inferencia se ejecuta localmente.

## Alcance y limitaciones de esta versión
La selección de momentos es una heurística basada en densidad de palabras y palabras clave; no garantiza que cada clip sea viral ni sustituye una revisión humana. El encuadre vertical es un recorte centrado, no seguimiento automático de rostro/hablante. No incluye todavía editor de línea de tiempo, seguimiento inteligente, publicación social ni GPU.


## Configuración avanzada (v0.3.0)

La pantalla Configuración permite guardar automáticamente y de forma persistente:
- Whisper tiny/base/small, duración de clips de 15 a 90 segundos y cantidad de 1 a 50.
- Subtítulos incrustados y orientación 9:16, 16:9 o 1:1.
- Resolución según orientación: vertical 1080x1920, 720x1280 o 480x854; horizontal 1920x1080, 1280x720 o 854x480.
- Audio original, normalización o silencio; bitrate AAC configurable.
- Perfiles de codificación rápido, equilibrado, máxima calidad y optimizado para CPU.
- Carpeta de destino, MP4/MKV, subcarpetas por proyecto y política para archivos existentes.

Las opciones de análisis se aplican al siguiente análisis y las opciones de exportación al siguiente lote exportado. El archivo fuente no se elimina.
\n\n## Preparar distribución Windows\nConsulta `BUILD_WINDOWS.md` y ejecuta `build_windows.bat` desde Windows.\n\n## Validación\nEjecuta `python -m unittest discover -s tests -v` para probar SQLite, selección de candidatos y una exportación real con FFmpeg. Para construir el EXE en Windows sigue `BUILD_WINDOWS.md`.\n