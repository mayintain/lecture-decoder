from datetime import datetime
from urllib.parse import quote

from app.core.config import TASKS_DIR


def list_previous_transcriptions() -> list[dict]:
    files = sorted(
        TASKS_DIR.glob("*_transcription.pdf"),
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )

    history = []

    for path in files:
        stat = path.stat()

        history.append({
            "filename": path.name,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "size_kb": round(stat.st_size / 1024, 1),
            "view_url": f"/view/{quote(path.name)}",
            "download_url": f"/download/{quote(path.name)}"
        })

    return history
