# REELMAKER 0.3.0

## Configuración avanzada
- Whisper tiny/base/small.
- Duración 15/30/45/60/90 segundos y cantidad 1/5/10/15/20/30/40/50.
- Subtítulos incrustados configurables.
- Orientación vertical 9:16, horizontal 16:9 y cuadrada 1:1.
- Resoluciones adaptadas a la orientación (incluye 480x854 vertical y 854x480 horizontal).
- Audio original, normalización de volumen o exportación sin audio.
- Bitrate AAC de 96/128/192/256 kbps.
- Perfiles de codificación rápido, equilibrado, máxima calidad y optimizado para CPU.
- MP4/MKV, carpeta de destino, organización por proyecto y renombrado/sobrescritura.
- Preferencias persistentes mediante QSettings y guardado automático.

## Seguridad
- Los vídeos fuente nunca se eliminan; la aplicación conserva el original.
- Los archivos existentes se renombran de forma predeterminada para evitar sobrescrituras accidentales.

## Verificación
- Se compiló sintácticamente cada archivo Python del proyecto.
- No se ejecutó una prueba completa de interfaz ni una exportación real en este entorno porque PySide6/FFmpeg de la instalación del usuario no están disponibles aquí.
