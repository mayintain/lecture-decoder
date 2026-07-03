from app.core.config import WHISPER_ENGINE
from app.services.platform_service import get_selected_engine


_engine = None


def get_transcriber_engine():
    global _engine

    if _engine is not None:
        return _engine

    engine_name = get_selected_engine() if WHISPER_ENGINE == "auto" else WHISPER_ENGINE

    if engine_name == "faster_whisper":
        from app.engines.faster_whisper_engine import FasterWhisperEngine

        _engine = FasterWhisperEngine()
        return _engine

    if engine_name == "mlx_whisper":
        from app.engines.mlx_whisper_engine import MlxWhisperEngine

        _engine = MlxWhisperEngine()
        return _engine

    raise ValueError(f"Unknown whisper engine: {engine_name}")
