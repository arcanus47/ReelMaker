import os
import sys
from pathlib import Path

APP_NAME = "REELMAKER"
APP_VERSION = "0.3.1"

if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    if os.name == "nt":
        DATA_HOME = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / APP_NAME
    else:
        DATA_HOME = Path.home() / ".reelmaker"
else:
    RESOURCE_DIR = Path(__file__).resolve().parent.parent
    DATA_HOME = RESOURCE_DIR

ASSETS_DIR = RESOURCE_DIR / "assets"
PROJECTS_DIR = DATA_HOME / "projects"
EXPORTS_DIR = DATA_HOME / "exports"
TEMP_DIR = DATA_HOME / "temp"
MODELS_DIR = DATA_HOME / "models"
LOGS_DIR = DATA_HOME / "logs"
DATABASE_PATH = DATA_HOME / "reelmaker.db"
FFMPEG_DIR = RESOURCE_DIR / "ffmpeg" / "bin"

for directory in (DATA_HOME, PROJECTS_DIR, EXPORTS_DIR, TEMP_DIR, MODELS_DIR, LOGS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

if FFMPEG_DIR.is_dir():
    os.environ["PATH"] = str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", "")

os.environ.setdefault("HF_HOME", str(MODELS_DIR))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(MODELS_DIR / "hub"))
