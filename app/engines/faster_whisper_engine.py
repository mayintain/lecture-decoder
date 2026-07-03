from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import WHISPER_COMPUTE_TYPE, WHISPER_CPU_THREADS
from app.engines.base import BaseTranscriber
from app.services.platform_service import get_recommended_cpu_threads
from app.core.utils import format_time


class FasterWhisperEngine(BaseTranscriber):
    def __init__(self):
        self.models = {}

    def _get_model(self, model_size: str) -> WhisperModel:
        if model_size not in self.models:
            cpu_threads = WHISPER_CPU_THREADS or get_recommended_cpu_threads() or 2

            print(f"[ENGINE] faster-whisper CPU")
            print(f"[ENGINE] model: {model_size}")
            print(f"[ENGINE] compute_type: {WHISPER_COMPUTE_TYPE}")
            print(f"[ENGINE] cpu_threads: {cpu_threads}")

            self.models[model_size] = WhisperModel(
                model_size,
                device="cpu",
                compute_type=WHISPER_COMPUTE_TYPE,
                cpu_threads=cpu_threads
            )

        return self.models[model_size]

    def transcribe(
        self,
        audio_path: Path,
        model_size: str = "large-v3-turbo",
        diarize: bool = False
    ) -> dict:
        model = self._get_model(model_size)

        segments, info = model.transcribe(
            str(audio_path),
            language="ru",
            task="transcribe",
            beam_size=4,
            temperature=0,
            condition_on_previous_text=True,
            vad_filter=False
        )

        lines = []
        structured_segments = []

        for segment in segments:
            start = format_time(segment.start)
            end = format_time(segment.end)
            text = segment.text.strip()

            if not text:
                continue

            line = f"[{start} - {end}] {text}"
            lines.append(line)

            structured_segments.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": text,
                    "speaker": None
                }
            )

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "model_size": model_size,
            "diarize": diarize,
            "lines": lines,
            "segments": structured_segments
        }

