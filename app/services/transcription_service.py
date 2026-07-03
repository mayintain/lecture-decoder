import time
from pathlib import Path

from app.core.config import (
    MAX_DIRECT_AUDIO_MINUTES,
    CHUNK_DURATION_MINUTES,
    COOL_DOWN_SECONDS
)
from app.engines.factory import get_transcriber_engine
from app.services.chunk_service import (
    get_audio_duration_seconds,
    split_audio_into_chunks
)
from app.services.correction_service import clean_transcription_result
from app.services.block_service import build_transcript_blocks


def transcribe_audio_file(
    audio_path: Path,
    model_size: str,
    diarize: bool = False
) -> dict:
    duration_seconds = get_audio_duration_seconds(audio_path)
    duration_minutes = duration_seconds / 60

    engine = get_transcriber_engine()

    print(f"[INFO] Audio duration: {duration_minutes:.2f} minutes")

    if duration_minutes <= MAX_DIRECT_AUDIO_MINUTES:
        print("[INFO] Mode: fast direct transcription")

        raw_result = engine.transcribe(
            audio_path,
            model_size=model_size,
            diarize=diarize
        )

        raw_result["processing_mode"] = "fast"
        raw_result["audio_duration_seconds"] = duration_seconds

        print("[POSTPROCESSING] Default noise cleanup on CPU")
        return clean_transcription_result(raw_result)

    print("[INFO] Mode: cool chunked transcription")
    print(f"[INFO] Chunk duration: {CHUNK_DURATION_MINUTES} minutes")
    print(f"[INFO] Cool down: {COOL_DOWN_SECONDS} seconds")

    chunks = split_audio_into_chunks(audio_path, CHUNK_DURATION_MINUTES)

    all_raw_lines = []
    all_cleaned_lines = []
    all_raw_segments = []
    all_cleaned_segments = []

    language = "ru"
    language_probability = None

    for chunk_number, chunk in enumerate(chunks, start=1):
        print(f"[PROCESSING] Chunk {chunk_number}/{len(chunks)}")

        raw_chunk_result = engine.transcribe(
            chunk["path"],
            model_size=model_size,
            diarize=diarize
        )

        language = raw_chunk_result.get("language", language)
        language_probability = raw_chunk_result.get(
            "language_probability",
            language_probability
        )

        shifted_chunk_result = shift_chunk_timestamps(
            raw_chunk_result,
            offset_seconds=chunk["offset_seconds"]
        )

        print(f"[POSTPROCESSING] Default noise cleanup for chunk {chunk_number}/{len(chunks)} on CPU")
        cleaned_chunk_result = clean_transcription_result(shifted_chunk_result)

        all_raw_lines.extend(cleaned_chunk_result.get("raw_lines", []))
        all_cleaned_lines.extend(cleaned_chunk_result.get("cleaned_lines", []))
        all_raw_segments.extend(cleaned_chunk_result.get("raw_segments", []))
        all_cleaned_segments.extend(cleaned_chunk_result.get("cleaned_segments", []))

        if chunk_number < len(chunks):
            print(f"[COOL DOWN] Sleeping for {COOL_DOWN_SECONDS} seconds")
            time.sleep(COOL_DOWN_SECONDS)

    return {
        "language": language,
        "language_probability": language_probability,
        "model_size": model_size,
        "diarize": diarize,
        "processing_mode": "cool_chunked",
        "audio_duration_seconds": duration_seconds,
        "chunk_duration_minutes": CHUNK_DURATION_MINUTES,
        "cool_down_seconds": COOL_DOWN_SECONDS,
        "chunks_count": len(chunks),
        "postprocessing_enabled": True,
        "postprocessing_mode": "default_noise_cleanup",

        "raw_lines": all_raw_lines,
        "cleaned_lines": all_cleaned_lines,
        "raw_segments": all_raw_segments,
        "cleaned_segments": all_cleaned_segments,
        "blocks": build_transcript_blocks(all_cleaned_segments),

        "lines": all_cleaned_lines,
        "segments": all_cleaned_segments
    }


def shift_chunk_timestamps(result: dict, offset_seconds: float) -> dict:
    shifted_result = dict(result)

    shifted_segments = []
    shifted_lines = []

    for segment in result.get("segments", []):
        shifted_start = float(segment["start"]) + offset_seconds
        shifted_end = float(segment["end"]) + offset_seconds
        text = segment["text"].strip()

        if not text:
            continue

        shifted_segment = dict(segment)
        shifted_segment["start"] = shifted_start
        shifted_segment["end"] = shifted_end
        shifted_segment["text"] = text

        shifted_segments.append(shifted_segment)
        shifted_lines.append(
            f"[{format_time(shifted_start)} - {format_time(shifted_end)}] {text}"
        )

    shifted_result["segments"] = shifted_segments
    shifted_result["lines"] = shifted_lines

    return shifted_result


def format_time(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"
