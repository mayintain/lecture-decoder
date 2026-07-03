import re


def build_transcript_blocks(
    segments: list[dict],
    max_gap_seconds: float = 2.8,
    max_block_duration_seconds: float = 35.0,
    max_block_chars: int = 420
) -> list[dict]:
    """
    Groups small Whisper segments into readable transcript blocks.

    A new block starts when:
    - there is a long pause between segments
    - current block is already too long
    - current block has too much text
    - previous text looks like a completed sentence and block is not tiny
    """
    blocks = []
    current = None

    for segment in segments:
        text = str(segment.get("text", "")).strip()
        if not text:
            continue

        start = float(segment.get("start", 0))
        end = float(segment.get("end", start))

        if current is None:
            current = create_block(start, end, text, segment)
            continue

        gap = start - current["end"]
        new_duration = end - current["start"]
        new_chars = len(current["text"]) + 1 + len(text)

        should_split = False

        if gap > max_gap_seconds:
            should_split = True

        if new_duration > max_block_duration_seconds:
            should_split = True

        if new_chars > max_block_chars:
            should_split = True

        if looks_like_sentence_end(current["text"]) and current_duration(current) >= 10:
            should_split = True

        if should_split:
            blocks.append(finalize_block(current))
            current = create_block(start, end, text, segment)
        else:
            current["end"] = end
            current["text"] = join_text(current["text"], text)
            current["segments"].append(segment)

    if current is not None:
        blocks.append(finalize_block(current))

    return blocks


def create_block(start: float, end: float, text: str, segment: dict) -> dict:
    return {
        "start": start,
        "end": end,
        "text": text,
        "segments": [segment]
    }


def finalize_block(block: dict) -> dict:
    block = dict(block)
    block["text"] = normalize_spaces(block["text"])
    block["start_time"] = format_time(block["start"])
    block["end_time"] = format_time(block["end"])
    block["time_range"] = f'{block["start_time"]} — {block["end_time"]}'
    return block


def join_text(left: str, right: str) -> str:
    left = left.strip()
    right = right.strip()

    if not left:
        return right

    if not right:
        return left

    if left.endswith("-"):
        return left[:-1] + right

    return left + " " + right


def looks_like_sentence_end(text: str) -> bool:
    text = text.strip()
    if not text:
        return False

    return text.endswith((".", "!", "?", "…"))


def current_duration(block: dict) -> float:
    return float(block["end"]) - float(block["start"])


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
