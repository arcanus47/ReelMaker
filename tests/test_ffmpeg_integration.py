import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.core.video_manager import VideoManager


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg/FFprobe no están instalados")
class FFmpegIntegrationTests(unittest.TestCase):
    def test_inspect_and_export_video_with_subtitles(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.mp4"
            subtitles = root / "captions.srt"
            output = root / "clip.mp4"

            create = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=24:duration=3",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
                "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", str(source)
            ], capture_output=True, text=True)
            if create.returncode:
                self.skipTest("FFmpeg no dispone de los codificadores necesarios: " + create.stderr[-500:])

            subtitles.write_text(
                "1\n00:00:00,000 --> 00:00:02,500\nSubtítulo de prueba\n",
                encoding="utf-8"
            )
            info = VideoManager.inspect_video(source)
            self.assertEqual(info["resolution"], "320x240")
            result = VideoManager.export_clip(
                source, output, 0, 2.5, width=240, height=426,
                subtitle_file=subtitles, audio_mode="normalize",
                audio_bitrate="96k", performance="fast"
            )
            self.assertTrue(Path(result).is_file())

            probe = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries",
                "stream=codec_type,width,height", "-of", "json", str(output)
            ], capture_output=True, text=True, check=True)
            streams = __import__("json").loads(probe.stdout)["streams"]
            video = next(stream for stream in streams if stream["codec_type"] == "video")
            self.assertEqual((video["width"], video["height"]), (240, 426))
            self.assertTrue(any(stream["codec_type"] == "audio" for stream in streams))


if __name__ == "__main__":
    unittest.main()
