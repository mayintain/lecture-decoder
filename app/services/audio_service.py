import subprocess
from pathlib import Path

from app.core.config import TASKS_DIR


def prepare_audio_for_transcription(input_path: Path) -> Path:
    prepared_path = TASKS_DIR / f"{input_path.stem}_prepared.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        str(prepared_path)
    ]

    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return prepared_path
