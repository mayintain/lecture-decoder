from abc import ABC, abstractmethod
from pathlib import Path


class BaseTranscriber(ABC):
    @abstractmethod
    def transcribe(
        self,
        audio_path: Path,
        model_size: str = "small",
        diarize: bool = False
    ) -> dict:
        pass
