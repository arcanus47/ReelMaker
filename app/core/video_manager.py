import json
import shutil
import subprocess
from pathlib import Path


class VideoManager:
    SUPPORTED_FORMATS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

    @staticmethod
    def check_ffmpeg():
        return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None

    @staticmethod
    def _subtitle_filter_path(path):
        """Escape a subtitle path for FFmpeg's filter parser on Windows and POSIX."""
        value = str(Path(path).resolve()).replace("\\", "/")
        value = value.replace(":", r"\:")
        value = value.replace("'", r"\'")
        return value

    @staticmethod
    def inspect_video(video_path):
        path = Path(video_path)
        if not path.is_file():
            raise FileNotFoundError("El vídeo no existe o no es un archivo.")
        if path.suffix.lower() not in VideoManager.SUPPORTED_FORMATS:
            raise ValueError("Formato no compatible.")
        if not VideoManager.check_ffmpeg():
            raise RuntimeError(
                "No se encontró FFmpeg/FFprobe. Instala FFmpeg o comprueba que "
                "ffmpeg.exe y ffprobe.exe estén junto a REELMAKER."
            )
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration,size,format_name:stream=codec_type,width,height,r_frame_rate,codec_name",
            "-of", "json", str(path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=90)
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if not video_stream:
            raise ValueError("El archivo no contiene una pista de vídeo.")
        fmt = data.get("format", {})
        duration = float(fmt.get("duration") or 0)
        num, den = (video_stream.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
        fps = float(num) / float(den) if float(den) else 0
        return {
            "name": path.name, "path": str(path.resolve()), "duration": duration,
            "size": int(fmt.get("size") or 0),
            "resolution": f'{video_stream.get("width", 0)}x{video_stream.get("height", 0)}',
            "fps": round(fps, 3), "video_codec": video_stream.get("codec_name", "?"),
            "audio_codec": audio_stream.get("codec_name", "Sin audio"),
            "format": fmt.get("format_name", "")
        }

    @staticmethod
    def format_duration(seconds):
        seconds = max(0, int(float(seconds or 0)))
        hours, rem = divmod(seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}" if hours else f"{minutes:02}:{seconds:02}"

    @staticmethod
    def export_clip(source, output, start, end, width=1080, height=1920,
                    subtitle_file=None, audio_mode="original",
                    audio_bitrate="128k", performance="cpu"):
        duration = float(end) - float(start)
        if duration <= 0:
            raise ValueError("La duración del clip debe ser mayor que cero.")
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)

        vf = (
            f"scale={int(width)}:{int(height)}:force_original_aspect_ratio=increase,"
            f"crop={int(width)}:{int(height)},setsar=1"
        )
        if subtitle_file and Path(subtitle_file).is_file():
            sub_path = VideoManager._subtitle_filter_path(subtitle_file)
            vf += (
                f",subtitles='{sub_path}':force_style='FontName=Arial,FontSize=18,"
                "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,"
                "Outline=2,Shadow=1,Alignment=2,MarginV=100'"
            )

        profiles = {
            "fast": ("ultrafast", "26"),
            "balanced": ("veryfast", "23"),
            "quality": ("slow", "18"),
            "cpu": ("veryfast", "23")
        }
        preset, crf = profiles.get(performance, profiles["cpu"])
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", str(max(0, float(start))), "-i", str(source),
            "-t", str(duration), "-map", "0:v:0"
        ]
        if audio_mode != "none":
            cmd += ["-map", "0:a?"]
        cmd += ["-vf", vf, "-c:v", "libx264", "-preset", preset, "-crf", crf]
        if output.suffix.lower() == ".mp4":
            cmd += ["-movflags", "+faststart"]
        if audio_mode == "none":
            cmd += ["-an"]
        else:
            cmd += ["-c:a", "aac", "-b:a", str(audio_bitrate)]
            if audio_mode == "normalize":
                cmd += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"]
        cmd.append(str(output))
        subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            timeout=max(300, int(duration * 12))
        )
        return str(output.resolve())
