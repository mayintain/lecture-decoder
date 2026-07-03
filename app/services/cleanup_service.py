import shutil
from pathlib import Path

from app.core.config import TASKS_DIR


def delete_file_safely(path: Path | None) -> None:
    if path is None:
        return

    try:
        if path.exists() and path.is_file():
            path.unlink()
    except Exception as error:
        print(f"[CLEANUP WARNING] Could not delete file {path}: {error}")


def delete_folder_safely(path: Path | None) -> None:
    if path is None:
        return

    try:
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
    except Exception as error:
        print(f"[CLEANUP WARNING] Could not delete folder {path}: {error}")


def cleanup_temp_audio_files(
    uploaded_audio_path: Path | None,
    prepared_audio_path: Path | None
) -> None:
    delete_file_safely(uploaded_audio_path)
    delete_file_safely(prepared_audio_path)

    if prepared_audio_path is not None:
        chunk_folder = TASKS_DIR / "chunks" / prepared_audio_path.stem
        delete_folder_safely(chunk_folder)
