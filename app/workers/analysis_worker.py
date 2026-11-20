from PySide6.QtCore import QThread, Signal


def prepare_pyav_compatibility():
    """
    Compatibilidad entre faster-whisper y versiones de PyAV cuya función
    av.open() ya no acepta el argumento metadata_errors.
    """
    import av

    if getattr(av, "_reelmaker_open_compat", False):
        return

    original_open = av.open

    def compatible_open(*args, **kwargs):
        # faster-whisper añade metadata_errors="ignore". En algunas versiones
        # de PyAV ese argumento no existe; retirarlo no impide decodificar audio.
        kwargs.pop("metadata_errors", None)
        return original_open(*args, **kwargs)

    av.open = compatible_open
    av._reelmaker_open_compat = True


class AnalysisWorker(QThread):
    progress = Signal(str)
    completed = Signal(list, list)
    failed = Signal(str)

    def __init__(self, video_path, model_size="base", clip_duration=30, clip_count=10):
        super().__init__()
        self.video_path = video_path
        self.model_size = model_size
        self.clip_duration = int(clip_duration)
        self.clip_count = int(clip_count)

    def run(self):
        try:
            self.progress.emit("Preparando motor de audio…")
            prepare_pyav_compatibility()

            self.progress.emit(f"Cargando Whisper ({self.model_size}) en CPU…")
            from faster_whisper import WhisperModel

            model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
                cpu_threads=2,
                num_workers=1
            )

            self.progress.emit(
                "Transcribiendo audio. El primer uso requiere descargar el modelo…"
            )
            segments, info = model.transcribe(
                self.video_path,
                beam_size=1,
                vad_filter=True
            )

            transcript = []
            for seg in segments:
                text = seg.text.strip()
                if text:
                    transcript.append({
                        "start": float(seg.start),
                        "end": float(seg.end),
                        "text": text
                    })

            if not transcript:
                raise RuntimeError(
                    "Whisper no detectó voz en el vídeo. Comprueba que el vídeo "
                    "tenga audio y que el volumen sea suficiente."
                )

            clips = build_candidates(
                transcript,
                info.duration if info.duration else transcript[-1]["end"],
                clip_duration=self.clip_duration,
                max_clips=self.clip_count
            )
            self.completed.emit(transcript, clips)

        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")


def build_candidates(segments, duration, clip_duration=30, max_clips=10):
    """Genera ventanas de duración configurable y prioriza las de mayor densidad verbal."""
    candidates = []
    duration = float(duration or segments[-1]["end"])
    clip_duration = max(10, int(clip_duration))
    max_clips = max(1, int(max_clips))
    hooks = (
        "porque", "pero", "cómo", "por qué", "nunca", "siempre",
        "increíble", "importante", "error", "secreto", "descubre", "resultado"
    )

    # Ventanas solapadas para no limitar el análisis a bloques rígidos.
    step = max(5.0, clip_duration * 0.65)
    start = 0.0
    while start < duration:
        end = min(duration, start + clip_duration)
        if end - start < min(10, clip_duration * 0.6):
            break

        found = [
            segment for segment in segments
            if segment["end"] > start and segment["start"] < end
        ]
        text = " ".join(segment["text"] for segment in found).strip()
        if text:
            words = text.split()
            density = len(words) / max(1, end - start)
            bonus = sum(1 for word in hooks if word in text.lower())
            # Evita premiar clips prácticamente vacíos.
            score = min(100, density * 7 + bonus * 5)
            candidates.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "title": " ".join(words[:8])[:72],
                "score": round(score, 1)
            })
        start += step

    # Quita candidatos demasiado parecidos entre sí, conservando el mejor puntuado.
    selected = []
    for candidate in sorted(candidates, key=lambda item: item["score"], reverse=True):
        overlaps = False
        for chosen in selected:
            intersection = max(
                0.0,
                min(candidate["end"], chosen["end"]) -
                max(candidate["start"], chosen["start"])
            )
            shorter = min(
                candidate["end"] - candidate["start"],
                chosen["end"] - chosen["start"]
            )
            if shorter > 0 and intersection / shorter > 0.65:
                overlaps = True
                break
        if not overlaps:
            selected.append(candidate)
        if len(selected) >= max_clips:
            break

    return sorted(selected, key=lambda item: item["start"])
