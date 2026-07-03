import json
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
        json_path = TASKS_DIR / path.name.replace("_transcription.pdf", "_transcription.json")
        display_name = path.name

        if json_path.exists() and json_path.is_file():
            with open(json_path, "r", encoding="utf-8") as file:
                metadata = json.load(file)
                display_name = metadata.get("source_filename") or path.name

        history.append({
            "filename": path.name,
            "display_name": display_name,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "size_kb": round(stat.st_size / 1024, 1),
            "view_url": f"/view/{quote(path.name)}",
            "download_url": f"/download/{quote(path.name)}"
        })

    return history
