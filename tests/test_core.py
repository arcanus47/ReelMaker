import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

# El test del algoritmo no necesita la interfaz gráfica; stub mínimo si PySide6
# no está instalado en la máquina que ejecuta estas pruebas unitarias.
try:
    import PySide6.QtCore  # noqa: F401
except ImportError:
    pyside = types.ModuleType("PySide6")
    qtcore = types.ModuleType("PySide6.QtCore")
    class DummySignal:
        def __init__(self, *args, **kwargs): pass
        def emit(self, *args, **kwargs): pass
    class DummyThread:
        def __init__(self, *args, **kwargs): pass
    qtcore.QThread = DummyThread
    qtcore.Signal = lambda *args, **kwargs: DummySignal()
    pyside.QtCore = qtcore
    sys.modules["PySide6"] = pyside
    sys.modules["PySide6.QtCore"] = qtcore

import app.database.database as database_module
from app.database.database import Database
from app.core.video_manager import VideoManager
from app.workers.analysis_worker import build_candidates
from app.workers.live_clipping_worker import LiveClippingWorker


class DatabaseTests(unittest.TestCase):
    def test_project_transcript_and_clip_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            import app.config as config
            original = database_module.DATABASE_PATH
            database_module.DATABASE_PATH = Path(tmp) / "test.db"
            try:
                db = Database()
                pid = db.create_project("test", "/tmp/source.mp4", 120, "1920x1080", 30)
                db.save_transcript(pid, [{"start": 0, "end": 2, "text": "Hola mundo"}])
                db.save_clips(pid, [{"title": "Clip", "start": 0, "end": 2, "score": 10}])
                self.assertEqual(len(db.get_projects()), 1)
                self.assertEqual(len(db.get_transcript(pid)), 1)
                self.assertEqual(len(db.get_clips(pid)), 1)
                db.update_clip(db.get_clips(pid)[0]["id"], "Editado", 1, 3)
                self.assertEqual(db.get_clips(pid)[0]["title"], "Editado")
                db.delete_project(pid)
                self.assertEqual(len(db.get_projects()), 0)
                db.close()
            finally:
                database_module.DATABASE_PATH = original


class CandidateTests(unittest.TestCase):
    def test_candidate_count_and_bounds(self):
        segments = [
            {"start": 0, "end": 12, "text": "Esto es una prueba importante porque funciona"},
            {"start": 15, "end": 28, "text": "Otro momento interesante con un resultado excelente"},
            {"start": 32, "end": 45, "text": "Un tercer segmento de prueba"}
        ]
        clips = build_candidates(segments, 50, clip_duration=15, max_clips=2)
        self.assertLessEqual(len(clips), 2)
        for clip in clips:
            self.assertGreater(clip["end"], clip["start"])
            self.assertLessEqual(clip["end"], 50)


class LiveClippingTests(unittest.TestCase):
    def test_safe_name_removes_path_and_special_characters(self):
        name = LiveClippingWorker._safe_name("../../A title: hello!")
        self.assertNotIn("/", name)
        self.assertNotIn(":", name)
        self.assertTrue(name)

    def test_youtube_cookie_profiles_exclude_web_creator_before_public_fallback(self):
        worker = LiveClippingWorker(
            "https://www.youtube.com/watch?v=example", "/tmp", browser_cookies="chrome"
        )
        profiles = worker._extraction_profiles()
        self.assertTrue(profiles[0][1])
        self.assertIn("web_creator", profiles[0][3]["youtube"]["player_client"][0])
        self.assertFalse(profiles[-1][1])
        self.assertTrue(any("HLS" in profile[0] for profile in profiles))

    def test_non_youtube_cookie_profile_does_not_add_youtube_extractor_args(self):
        worker = LiveClippingWorker(
            "https://example.com/live.m3u8", "/tmp", browser_cookies="firefox"
        )
        profiles = worker._extraction_profiles()
        self.assertEqual(len(profiles), 1)
        self.assertTrue(profiles[0][1])
        self.assertIsNone(profiles[0][3])

    def test_ffmpeg_command_uses_segment_muxer(self):
        from unittest.mock import patch
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            worker = LiveClippingWorker(
                "https://example.com/live", tmp, segment_minutes=3
            )
            worker._segments_dir = Path(tmp)
            with patch("app.workers.live_clipping_worker.shutil.which", return_value="/usr/bin/ffmpeg"):
                command = worker._build_ffmpeg_command([("https://cdn.example/live.m3u8", {})])
            self.assertIn("segment", command)
            self.assertIn("180", command)
            self.assertIn("mpegts", command)


class VideoManagerTests(unittest.TestCase):
    def test_subtitle_path_escaping(self):
        escaped = VideoManager._subtitle_filter_path(Path("some folder") / "a.srt")
        self.assertIn("some folder", escaped)
        self.assertTrue(escaped.endswith("a.srt"))

    def test_invalid_clip_duration(self):
        with self.assertRaises(ValueError):
            VideoManager.export_clip("in.mp4", "out.mp4", 5, 5)

    def test_live_output_format_dimensions(self):
        self.assertEqual(VideoManager.dimensions_for_format("vertical"), (1080, 1920))
        self.assertEqual(VideoManager.dimensions_for_format("horizontal"), (1920, 1080))
        self.assertEqual(VideoManager.dimensions_for_format("square"), (1080, 1080))

    def test_unknown_live_output_format_is_rejected(self):
        with self.assertRaises(ValueError):
            VideoManager.dimensions_for_format("panoramic")


if __name__ == "__main__":
    unittest.main()
