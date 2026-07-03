from pathlib import Path

import mlx_whisper

from app.engines.base import BaseTranscriber
from app.core.utils import format_time


MODEL_REPOSITORIES = {
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "mlx-community/whisper-large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
    "mlx-community/whisper-large-v3-mlx": "mlx-community/whisper-large-v3-mlx",
}


class MlxWhisperEngine(BaseTranscriber):
    def transcribe(
        self,
        audio_path: Path,
        model_size: str = "large-v3-turbo",
        diarize: bool = False
    ) -> dict:
        model_repo = MODEL_REPOSITORIES.get(model_size, model_size)

        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=model_repo,
            language="ru",
            task="transcribe",
            verbose=False
        )

        raw_segments = result.get("segments", [])

        lines = []
        structured_segments = []

        for segment in raw_segments:
            start_seconds = float(segment.get("start", 0))
            end_seconds = float(segment.get("end", 0))
            text = segment.get("text", "").strip()

            if not text:
                continue

            start = format_time(start_seconds)
            end = format_time(end_seconds)

            lines.append(f"[{start} - {end}] {text}")

            structured_segments.append(
                {
                    "start": start_seconds,
                    "end": end_seconds,
                    "text": text,
                    "speaker": None
                }
            )

        if not lines and result.get("text"):
            text = result["text"].strip()
            lines.append(text)

            structured_segments.append(
                {
                    "start": 0.0,
                    "end": 0.0,
                    "text": text,
                    "speaker": None
                }
            )

        return {
            "language": result.get("language", "ru"),
            "language_probability": 1,
            "model_size": model_size,
            "engine_model": model_repo,
            "diarize": diarize,
            "lines": lines,
            "segments": structured_segments
        }

