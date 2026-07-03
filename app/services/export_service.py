import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from app.core.config import BASE_DIR, TASKS_DIR


def save_transcription(audio_path: Path, result: dict, source_filename: str | None = None) -> Path:
    pdf_file_path = TASKS_DIR / f"{audio_path.stem}_transcription.pdf"
    json_file_path = TASKS_DIR / f"{audio_path.stem}_transcription.json"

    display_filename = source_filename or audio_path.name

    result["source_filename"] = display_filename
    result["pdf_filename"] = pdf_file_path.name

    with open(json_file_path, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    save_transcription_pdf(
        pdf_file_path=pdf_file_path,
        source_filename=display_filename,
        result=result
    )

    return pdf_file_path


def save_transcription_pdf(
    pdf_file_path: Path,
    source_filename: str,
    result: dict
) -> None:
    font_name = register_readable_font()

    doc = SimpleDocTemplate(
        str(pdf_file_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=16,
        leading=20,
        spaceAfter=12
    )

    time_style = ParagraphStyle(
        "TimeCustom",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=13,
        textColor="#555555",
        spaceBefore=8,
        spaceAfter=3
    )

    text_style = ParagraphStyle(
        "TextCustom",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=16,
        spaceAfter=8
    )

    story = []

    story.append(Paragraph(escape_text(f"Файл: {source_filename}"), title_style))
    story.append(Spacer(1, 6))

    blocks = result.get("blocks", [])

    if blocks:
        for block in blocks:
            time_range = block.get("time_range", "")
            text = block.get("text", "")

            if not text:
                continue

            story.append(Paragraph(escape_text(f"[{time_range}]"), time_style))
            story.append(Paragraph(escape_text(text), text_style))
    else:
        for line in result.get("cleaned_lines", result.get("lines", [])):
            story.append(Paragraph(escape_text(line), text_style))

    doc.build(story)


def register_readable_font() -> str:
    candidates = [
        BASE_DIR / "app" / "static" / "fonts" / "ReadableFont.ttf",
        BASE_DIR / "app" / "static" / "fonts" / "PTFreeSans.ttf",
        BASE_DIR / "app" / "static" / "fonts" / "DejaVuSans.ttf",
        BASE_DIR / "app" / "static" / "fonts" / "Inter.ttf",
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
    ]

    for font_path in candidates:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont("ReadableFont", str(font_path)))
            return "ReadableFont"

    raise RuntimeError(
        "No Cyrillic-compatible PDF font found. "
        "Add a .ttf font file to app/static/fonts/ReadableFont.ttf."
    )


def escape_text(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )
