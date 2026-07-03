from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]

STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
TASKS_DIR = STORAGE_DIR / "tasks"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
TASKS_DIR.mkdir(parents=True, exist_ok=True)

WHISPER_ENGINE = os.getenv("WHISPER_ENGINE", "auto")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_CPU_THREADS_RAW = os.getenv("WHISPER_CPU_THREADS")
WHISPER_CPU_THREADS = int(WHISPER_CPU_THREADS_RAW) if WHISPER_CPU_THREADS_RAW else None


MAX_DIRECT_AUDIO_MINUTES = int(os.getenv("MAX_DIRECT_AUDIO_MINUTES", "25"))
CHUNK_DURATION_MINUTES = int(os.getenv("CHUNK_DURATION_MINUTES", "15"))
COOL_DOWN_SECONDS = int(os.getenv("COOL_DOWN_SECONDS", "30"))

