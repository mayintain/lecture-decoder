import re
from copy import deepcopy

from app.services.block_service import build_transcript_blocks


def clean_transcription_result(result: dict) -> dict:
    cleaned_result = deepcopy(result)

    raw_lines = result.get("lines", [])
    raw_segments = result.get("segments", [])

    cleaned_lines = []
    cleaned_segments = []

    previous_texts = []

    for segment in raw_segments:
        raw_text = segment.get("text", "").strip()
        cleaned_text = clean_text(raw_text)

        if not cleaned_text:
            continue

        if is_repeated_nearby(cleaned_text, previous_texts):
            continue

        previous_texts.append(cleaned_text)
        previous_texts = previous_texts[-5:]

        cleaned_segment = dict(segment)
        cleaned_segment["raw_text"] = raw_text
        cleaned_segment["cleaned_text"] = cleaned_text
        cleaned_segment["text"] = cleaned_text

        cleaned_segments.append(cleaned_segment)

        start = format_time(float(cleaned_segment["start"]))
        end = format_time(float(cleaned_segment["end"]))
        cleaned_lines.append(f"[{start} - {end}] {cleaned_text}")

    cleaned_result["raw_lines"] = raw_lines
    cleaned_result["raw_segments"] = raw_segments

    cleaned_result["cleaned_lines"] = cleaned_lines
    cleaned_result["cleaned_segments"] = cleaned_segments

    cleaned_result["lines"] = cleaned_lines
    cleaned_result["segments"] = cleaned_segments
    cleaned_result["blocks"] = build_transcript_blocks(cleaned_segments)

    cleaned_result["postprocessing_enabled"] = True
    cleaned_result["postprocessing_mode"] = "default_noise_cleanup"

    return cleaned_result


def clean_text(text: str) -> str:
    text = text.strip()

    if not text:
        return ""

    text = normalize_spaces(text)
    text = remove_repeated_character_noise(text)
    text = remove_repeated_phrase_tail(text)
    text = normalize_spaces(text)

    if not text:
        return ""

    if is_garbage_text(text):
        return ""

    return text


def remove_repeated_character_noise(text: str) -> str:
    text = re.sub(r"([A-Za-zА-Яа-яЁё]{1,3})\1{8,}.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"([A-Za-zА-Яа-яЁё])\1{10,}.*$", "", text, flags=re.IGNORECASE)

    text = re.sub(r"(.)\1{20,}", "", text)

    return text.strip()


def remove_repeated_phrase_tail(text: str) -> str:
    words = re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", text)

    if len(words) < 6:
        return text

    lower_words = [word.lower() for word in words]

    if len(lower_words) >= 6 and len(set(lower_words)) <= 2:
        return ""

    for phrase_len in range(1, 6):
        if len(lower_words) < phrase_len * 3:
            continue

        phrase = lower_words[:phrase_len]
        repeated = True

        for i in range(0, min(len(lower_words), phrase_len * 5), phrase_len):
            if lower_words[i:i + phrase_len] != phrase:
                repeated = False
                break

        if repeated:
            return ""

    return text.strip()


def is_repeated_nearby(text: str, previous_texts: list[str]) -> bool:
    normalized = normalize_for_compare(text)

    for previous in previous_texts:
        previous_normalized = normalize_for_compare(previous)

        if normalized == previous_normalized:
            return True

        if len(normalized) < 80 and similarity(normalized, previous_normalized) > 0.92:
            return True

    return False


def is_garbage_text(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)

    if not compact:
        return True

    if len(compact) >= 25 and len(set(compact.upper())) <= 3:
        return True

    words = re.findall(r"[A-Za-zА-Яа-яЁё]+", text.lower())

    if len(words) >= 8 and len(set(words)) <= 2:
        return True

    return False


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    shorter = min(len(a), len(b))
    longer = max(len(a), len(b))

    same = sum(1 for x, y in zip(a, b) if x == y)

    return same / longer if longer else 0.0


def normalize_for_compare(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-zа-яё0-9]+", "", text)
    return text


def normalize_spaces(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text.strip()


def format_time(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"
