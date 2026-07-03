import shutil
import subprocess
from pathlib import Path

from app.core.config import TASKS_DIR


CHUNKS_DIR = TASKS_DIR / "chunks"
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


def get_audio_duration_seconds(audio_path: Path) -> float:
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]

    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True
    )

    return float(result.stdout.strip())


def split_audio_into_chunks(audio_path: Path, chunk_duration_minutes: int) -> list[dict]:
    duration_seconds = get_audio_duration_seconds(audio_path)
    chunk_duration_seconds = chunk_duration_minutes * 60

    chunk_folder = CHUNKS_DIR / audio_path.stem

    if chunk_folder.exists():
        shutil.rmtree(chunk_folder)

    chunk_folder.mkdir(parents=True, exist_ok=True)

    chunks = []
    start_seconds = 0.0
    chunk_index = 1

    while start_seconds < duration_seconds:
        chunk_path = chunk_folder / f"chunk_{chunk_index:03d}.wav"

        command = [
            "ffmpeg",
            "-y",
            "-ss", str(start_seconds),
            "-i", str(audio_path),
            "-t", str(chunk_duration_seconds),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            str(chunk_path)
        ]

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        chunks.append(
            {
                "index": chunk_index,
                "path": chunk_path,
                "offset_seconds": start_seconds
            }
        )

        start_seconds += chunk_duration_seconds
        chunk_index += 1

    return chunks
