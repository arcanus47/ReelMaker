import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.config import TEMP_DIR
from app.core.video_manager import VideoManager
from app.workers.analysis_worker import prepare_pyav_compatibility, build_candidates


class LiveClippingWorker(QThread):
    status = Signal(str)
    clip_generated = Signal(str, str, float)
    failed = Signal(str)
    finished_summary = Signal(int, str)

    def __init__(
        self, stream_url, output_dir, model_size="base", segment_minutes=5,
        clip_duration=30, clips_per_segment=1, browser_cookies="",
        keep_segments=False, subtitles=True, output_format="vertical"
    ):
        super().__init__()
        self.stream_url = stream_url.strip()
        self.output_dir = Path(output_dir).expanduser()
        self.model_size = model_size
        self.segment_seconds = int(segment_minutes) * 60
        self.clip_duration = int(clip_duration)
        self.clips_per_segment = int(clips_per_segment)
        self.browser_cookies = browser_cookies or ""
        self.keep_segments = bool(keep_segments)
        self.subtitles = bool(subtitles)
        self.output_format = str(output_format or "vertical").lower()
        self._stop_requested = False
        self._ffmpeg = None
        self._generated = 0
        self._next_segment_number = 0
        self._session_dir = Path(TEMP_DIR) / "live_sessions" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self._segments_dir = self._session_dir / "segments"

    def request_stop(self):
        self._stop_requested = True
        process = self._ffmpeg
        if process and process.poll() is None:
            try:
                if process.stdin:
                    process.stdin.write(b"q\n")
                    process.stdin.flush()
            except Exception:
                pass

    @staticmethod
    def _safe_name(value):
        value = re.sub(r"[^A-Za-z0-9_-]+", "_", value or "live_clip").strip("_")
        return (value[:48] or "live_clip")

    @staticmethod
    def _is_youtube_url(url):
        value = (url or "").lower()
        return any(host in value for host in (
            "youtube.com/", "youtu.be/", "youtube.com:", "youtube-nocookie.com/"
        ))

    def _extraction_profiles(self):
        """Perfiles ordenados para no perder formatos cuando YouTube recibe cookies.

        En YouTube, las sesiones autenticadas pueden activar clientes como
        web_creator, que en algunas cuentas/directos no devuelve formatos sin
        PO Token. Se prueba primero el conjunto predeterminado excluyendo ese
        cliente, favoreciendo HLS para directos, y después perfiles alternativos.
        La última opción sin cookies solo permite continuar si el contenido es
        público; no sustituye ni evade permisos de contenido privado.
        """
        youtube = self._is_youtube_url(self.stream_url)
        profiles = []
        if self.browser_cookies:
            if youtube:
                profiles.extend([
                    ("sesión · HLS", True, "best[protocol*=m3u8]/bestvideo*+bestaudio/best",
                     {"youtube": {"player_client": ["default,-web_creator"]}}),
                    ("sesión · formatos alternativos", True, "bestvideo*+bestaudio/best",
                     {"youtube": {"player_client": ["default,-web_creator"]}}),
                    ("sesión · predeterminado", True, "bestvideo*+bestaudio/best", None),
                ])
            else:
                profiles.append(("sesión", True, "bestvideo*+bestaudio/best", None))
            if youtube:
                profiles.extend([
                    ("acceso público · HLS", False, "best[protocol*=m3u8]/bestvideo*+bestaudio/best",
                     {"youtube": {"player_client": ["default,-web_creator"]}}),
                    ("acceso público · alternativo", False, "bestvideo*+bestaudio/best", None),
                ])
        else:
            if youtube:
                profiles.extend([
                    ("HLS", False, "best[protocol*=m3u8]/bestvideo*+bestaudio/best", None),
                    ("formatos alternativos", False, "bestvideo*+bestaudio/best", None),
                    ("predeterminado", False, "best/bestvideo+bestaudio", None),
                ])
            else:
                profiles.append(("predeterminado", False, "bestvideo*+bestaudio/best", None))
        return profiles

    def _resolve_stream(self):
        self.status.emit("Conectando con la plataforma y resolviendo la transmisión…")
        try:
            from yt_dlp import YoutubeDL
        except ImportError as exc:
            raise RuntimeError("Falta yt-dlp. Instala las dependencias con: pip install -r requirements.txt") from exc

        info = None
        errors = []
        profiles = self._extraction_profiles()
        for label, use_cookies, selector, extractor_args in profiles:
            self.status.emit(f"Resolviendo transmisión ({label})…")
            options = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "format": selector,
                "skip_download": True,
                "ignoreerrors": False,
            }
            if use_cookies:
                options["cookiesfrombrowser"] = (self.browser_cookies,)
            if extractor_args:
                options["extractor_args"] = extractor_args
            try:
                with YoutubeDL(options) as ydl:
                    candidate = ydl.extract_info(self.stream_url, download=False)
                if candidate:
                    info = candidate
                    if not use_cookies and self.browser_cookies:
                        self.status.emit(
                            "YouTube no entregó formatos con esa sesión; se encontró acceso público. "
                            "Continuando sin cookies (el contenido privado seguirá requiriendo una sesión válida)."
                        )
                    break
            except Exception as exc:
                # Guardar el diagnóstico sin códigos ANSI para que la UI/logs sean legibles.
                message = re.sub(r"\x1b\[[0-9;]*m", "", str(exc))
                errors.append(f"{label}: {message}")
        if not info:
            detail = errors[-1] if errors else "No se recibió información del enlace."
            if self.browser_cookies and self._is_youtube_url(self.stream_url):
                detail += (
                    "\n\nLa sesión del navegador puede estar caducada o YouTube puede exigir "
                    "un PO Token para los formatos de esa sesión. Prueba cerrar y volver a iniciar "
                    "sesión en el navegador, o selecciona 'No usar cookies' si el directo es público."
                )
            raise RuntimeError(
                "yt-dlp no pudo resolver un formato compatible. " + detail
            )

        formats = info.get("requested_formats") or []
        if not formats:
            formats = [info]
        inputs = []
        for fmt in formats:
            url = fmt.get("url")
            if not url:
                continue
            headers = fmt.get("http_headers") or info.get("http_headers") or {}
            inputs.append((url, headers))
        if not inputs:
            raise RuntimeError("La plataforma no entregó una URL de transmisión utilizable.")
        is_live = bool(info.get("is_live")) or info.get("live_status") == "is_live"
        return inputs, info.get("title") or info.get("id") or "directo", is_live

    def _build_ffmpeg_command(self, inputs):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("No se encontró FFmpeg. Instálalo y comprueba que ffmpeg esté en PATH.")
        command = [ffmpeg, "-hide_banner", "-loglevel", "warning", "-y"]
        for url, headers in inputs:
            if headers:
                header_text = "".join(f"{key}: {value}\r\n" for key, value in headers.items())
                command += ["-headers", header_text]
            command += ["-reconnect", "1", "-reconnect_streamed", "1",
                        "-reconnect_delay_max", "10", "-i", url]
        if len(inputs) > 1:
            command += ["-map", "0:v:0", "-map", "1:a:0?"]
        else:
            command += ["-map", "0:v:0", "-map", "0:a?"]
        command += [
            "-c", "copy",
            "-f", "segment",
            "-segment_format", "mpegts",
            "-segment_time", str(self.segment_seconds),
            "-reset_timestamps", "1",
            "-segment_start_number", str(self._next_segment_number),
            str(self._segments_dir / "segment_%06d.ts")
        ]
        return command

    def _write_srt(self, transcript, start, end, path):
        def stamp(seconds):
            millis = int(max(0, seconds) * 1000)
            hours, rem = divmod(millis, 3600000)
            minutes, rem = divmod(rem, 60000)
            secs, ms = divmod(rem, 1000)
            return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"

        rows = []
        for segment in transcript:
            a = max(float(start), float(segment["start"]))
            b = min(float(end), float(segment["end"]))
            if b <= a:
                continue
            rows.extend([
                str(len(rows) // 4 + 1),
                f"{stamp(a - start)} --> {stamp(b - start)}",
                segment["text"],
                ""
            ])
        if rows:
            path.write_text("\n".join(rows), encoding="utf-8")
            return str(path)
        return None

    def _process_segment(self, segment_path, model, stream_title, index):
        self.status.emit(f"Analizando segmento {index + 1}: {segment_path.name}…")
        segments, info = model.transcribe(
            str(segment_path), beam_size=1, vad_filter=True
        )
        transcript = []
        for item in segments:
            text = item.text.strip()
            if text:
                transcript.append({
                    "start": float(item.start),
                    "end": float(item.end),
                    "text": text
                })
        if not transcript:
            self.status.emit(f"Segmento {index + 1}: no se detectó voz; se continúa la captura.")
            if not self.keep_segments:
                segment_path.unlink(missing_ok=True)
            return

        duration = float(getattr(info, "duration", 0) or transcript[-1]["end"])
        candidates = build_candidates(
            transcript, duration,
            clip_duration=self.clip_duration,
            max_clips=self.clips_per_segment
        )
        for number, candidate in enumerate(candidates, 1):
            title = candidate.get("title") or f"Clip {index + 1}-{number}"
            filename = (
                f"live_{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                f"s{index + 1:05d}_{number:02d}_{self._safe_name(title)}.mp4"
            )
            output = self.output_dir / filename
            subtitle_path = self._session_dir / f"subtitle_{index}_{number}.srt"
            subtitle_file = None
            if self.subtitles:
                subtitle_file = self._write_srt(
                    transcript, candidate["start"], candidate["end"], subtitle_path
                )
            try:
                width, height = VideoManager.dimensions_for_format(self.output_format)
                VideoManager.export_clip(
                    segment_path, output,
                    candidate["start"], candidate["end"],
                    width=width, height=height,
                    subtitle_file=subtitle_file,
                    audio_mode="original",
                    audio_bitrate="128k",
                    performance="fast"
                )
            finally:
                if subtitle_path.exists():
                    subtitle_path.unlink()
            self._generated += 1
            self.clip_generated.emit(str(output), title, float(candidate["score"]))
        if not self.keep_segments:
            segment_path.unlink(missing_ok=True)

    def _process_finished_segments(self, model, stream_title, processed, segment_index, include_open=False):
        files = sorted(self._segments_dir.glob("segment_*.ts"))
        completed_files = files if include_open else (files[:-1] if files else [])
        for segment_path in completed_files:
            if segment_path.name in processed:
                continue
            processed.add(segment_path.name)
            self._process_segment(segment_path, model, stream_title, segment_index)
            segment_index += 1
            try:
                self._next_segment_number = max(
                    self._next_segment_number,
                    int(segment_path.stem.rsplit("_", 1)[-1]) + 1
                )
            except ValueError:
                self._next_segment_number += 1
        return segment_index

    def run(self):
        process = None
        model = None
        log_handle = None
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self._segments_dir.mkdir(parents=True, exist_ok=True)
            prepare_pyav_compatibility()
            processed = set()
            segment_index = 0
            reconnect_attempts = 0
            while not self._stop_requested:
                inputs, stream_title, is_live = self._resolve_stream()
                if self._stop_requested:
                    break

                command = self._build_ffmpeg_command(inputs)
                self.status.emit(
                    f"Captura activa: {stream_title}. Análisis cada "
                    f"{self.segment_seconds // 60} minuto(s)."
                )
                log_path = self._session_dir / "ffmpeg.log"
                if log_handle:
                    log_handle.close()
                log_handle = open(log_path, "a", encoding="utf-8", errors="replace")
                process = subprocess.Popen(
                    command, stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL, stderr=log_handle
                )
                self._ffmpeg = process

                # La captura comienza ANTES de descargar/cargar Whisper, evitando
                # perder el inicio del directo durante la descarga del modelo.
                if model is None:
                    self.status.emit(
                        f"Captura iniciada. Cargando Whisper {self.model_size}; "
                        "la primera vez puede tardar varios minutos…"
                    )
                    from faster_whisper import WhisperModel
                    model = WhisperModel(
                        self.model_size, device="cpu", compute_type="int8",
                        cpu_threads=max(1, min(4, os.cpu_count() or 2)), num_workers=1
                    )
                    self.status.emit("Whisper listo. Capturando y analizando segmentos…")

                while not self._stop_requested and process.poll() is None:
                    before = len(processed)
                    segment_index = self._process_finished_segments(
                        model, stream_title, processed, segment_index, include_open=False
                    )
                    if len(processed) > before:
                        reconnect_attempts = 0
                    self.msleep(1000)

                if process.poll() is None and self._stop_requested:
                    try:
                        if process.stdin:
                            process.stdin.write(b"q\\n")
                            process.stdin.flush()
                    except Exception:
                        pass
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)

                # Todos los segmentos de este proceso ya están cerrados.
                segment_index = self._process_finished_segments(
                    model, stream_title, processed, segment_index, include_open=True
                )
                return_code = process.returncode
                self._ffmpeg = None

                if self._stop_requested:
                    break
                if return_code in (0, None):
                    # Final normal de una transmisión/VOD.
                    break
                if not is_live:
                    try:
                        diagnostic = log_path.read_text(encoding="utf-8", errors="replace")[-1800:]
                    except Exception:
                        diagnostic = ""
                    raise RuntimeError(
                        "FFmpeg no pudo mantener la captura y el enlace no fue identificado como un directo. "
                        f"Código de salida: {return_code}.\n{diagnostic}"
                    )
                if reconnect_attempts >= 5:
                    raise RuntimeError(
                        "No se pudo recuperar la transmisión después de 5 intentos. "
                        "Comprueba tu conexión, la sesión y el enlace."
                    )

                reconnect_attempts += 1
                self.status.emit(
                    f"Conexión interrumpida. Reintentando {reconnect_attempts}/5; "
                    "se conservarán los clips y segmentos ya procesados…"
                )
                for _ in range(10):
                    if self._stop_requested:
                        break
                    self.msleep(500)

            self.finished_summary.emit(
                self._generated,
                "Captura detenida." if self._stop_requested else "La transmisión finalizó."
            )
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        finally:
            self._ffmpeg = None
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=10)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass
            if log_handle:
                try:
                    log_handle.close()
                except Exception:
                    pass
