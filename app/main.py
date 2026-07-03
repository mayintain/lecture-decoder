from pathlib import Path
import shutil
from uuid import uuid4
import json
from urllib.parse import quote

from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.core.config import UPLOADS_DIR, TASKS_DIR
from app.services.audio_service import prepare_audio_for_transcription
from app.services.cleanup_service import cleanup_temp_audio_files
from app.services.export_service import save_transcription
from app.services.history_service import list_previous_transcriptions
from app.services.platform_service import get_system_profile
from app.services.transcription_service import transcribe_audio_file


app = FastAPI(title="Lecture Decoder")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "result": None,
            "result_file_path": None,
            "result_filename": None,
            "previous_transcriptions": list_previous_transcriptions(),
            "system_info": get_system_profile()
        }
    )


@app.post("/transcribe", response_class=HTMLResponse)
def transcribe(
    request: Request,
    audio_file: UploadFile = File(...),
    model_size: str = Form("large-v3-turbo"),
    diarize: bool = Form(False)
):
    original_filename = Path(audio_file.filename).name
    unique_filename = f"{uuid4().hex}_{original_filename}"
    file_path = UPLOADS_DIR / unique_filename
    prepared_audio_path = None
    result = None
    result_file_path = None

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        prepared_audio_path = prepare_audio_for_transcription(file_path)

        result = transcribe_audio_file(
            prepared_audio_path,
            model_size=model_size,
            diarize=diarize
        )

        result_file_path = save_transcription(
            file_path,
            result,
            source_filename=original_filename
        )

    finally:
        cleanup_temp_audio_files(
            uploaded_audio_path=file_path,
            prepared_audio_path=prepared_audio_path
        )

    return RedirectResponse(
        url=f"/view/{quote(result_file_path.name)}",
        status_code=303
    )



@app.get("/view/{filename}", response_class=HTMLResponse)
def view_transcription(request: Request, filename: str):
    safe_filename = Path(filename).name

    if not safe_filename.endswith("_transcription.pdf"):
        return {"error": "Некорректный файл"}

    pdf_path = TASKS_DIR / safe_filename
    json_path = TASKS_DIR / safe_filename.replace("_transcription.pdf", "_transcription.json")

    if not pdf_path.exists() or not json_path.exists():
        return {"error": "Расшифровка не найдена"}

    with open(json_path, "r", encoding="utf-8") as file:
        result = json.load(file)

    return templates.TemplateResponse(
        request,
        "view_transcription.html",
        {
            "result": result,
            "blocks": result.get("blocks", []),
            "source_filename": result.get("source_filename", safe_filename),
            "pdf_filename": safe_filename
        }
    )


@app.get("/download/{filename}")
def download_result(filename: str):
    file_path = TASKS_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        return {"error": "Файл не найден"}

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        content_disposition_type="inline"
    )

@app.post("/delete/{filename}")
def delete_transcription_result(filename: str):
    safe_filename = Path(filename).name

    if not safe_filename.endswith("_transcription.pdf"):
        return RedirectResponse(url="/#history", status_code=303)

    pdf_path = TASKS_DIR / safe_filename
    json_path = TASKS_DIR / safe_filename.replace("_transcription.pdf", "_transcription.json")

    if pdf_path.exists() and pdf_path.is_file():
        pdf_path.unlink()

    if json_path.exists() and json_path.is_file():
        json_path.unlink()

    return RedirectResponse(url="/#history", status_code=303)


@app.post("/clear-history")
def clear_transcription_history():
    for path in TASKS_DIR.glob("*_transcription.pdf"):
        if path.is_file():
            path.unlink()

    for path in TASKS_DIR.glob("*_transcription.json"):
        if path.is_file():
            path.unlink()

    return RedirectResponse(url="/#history", status_code=303)

