# Informe de validación — REELMAKER 0.3.1

## Pruebas ejecutadas en este entorno Linux

Resultado: **5 pruebas aprobadas, 0 fallidas**.

1. SQLite: crear proyecto, guardar transcripción y clips, editar clip y eliminar proyecto.
2. Selección de candidatos: límite de cantidad y límites de tiempo.
3. VideoManager: rechaza clips con duración inválida.
4. Rutas de subtítulos: comprobación de la función de escape.
5. Integración FFmpeg real: generación de vídeo sintético, inspección con FFprobe, exportación H.264/AAC vertical con subtítulos incrustados y normalización de audio; FFprobe confirmó 240x426 y pista de audio.

También se ejecutó `compileall` sobre los archivos Python sin errores de sintaxis.

## Pruebas pendientes antes de publicar

Este entorno no tiene PySide6, faster-whisper ni PyInstaller instalados. Por eso todavía no se ha podido:
- abrir y recorrer la interfaz gráfica real;
- descargar modelos Whisper y ejecutar una transcripción real;
- construir el EXE Windows;
- probar el EXE en Windows limpio y validar todas las DLL de FFmpeg en ese sistema.

El flujo de construcción de Windows ejecuta las pruebas automáticas antes de invocar PyInstaller. Después del build hay que abrir `dist/REELMAKER/REELMAKER.exe`, importar un vídeo real, ejecutar Whisper y exportar un clip para validar el paquete final.
