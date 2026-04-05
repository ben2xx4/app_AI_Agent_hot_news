from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime


def normalize_whitespace(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def normalize_key(text: str | None) -> str:
    value = normalize_whitespace(text).lower()
    value = re.sub(r"[^a-z0-9a-zA-ZÀ-ỹ\s-]", "", value)
    return re.sub(r"\s+", "-", value).strip("-")


def stable_hash(*parts: str | None) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(normalize_whitespace(part).encode("utf-8"))
        digest.update(b"|")
    return digest.hexdigest()


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def normalize_datetime_for_compare(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def resolve_max_age_days(value: int | str | None) -> int | None:
    if value in {None, ""}:
        return None
    try:
        days = int(value)
    except (TypeError, ValueError):
        return None
    return days if days > 0 else None


def is_datetime_within_age_window(
    value: datetime | None,
    max_age_days: int | str | None,
    *,
    now_provider: Callable[[], datetime] | None = None,
) -> bool:
    resolved_days = resolve_max_age_days(max_age_days)
    if value is None or resolved_days is None:
        return True
    current_time = normalize_datetime_for_compare(
        now_provider() if now_provider is not None else datetime.now(UTC)
    )
    candidate_time = normalize_datetime_for_compare(value)
    return candidate_time >= current_time - timedelta(days=resolved_days)


def similarity_score(left: str | None, right: str | None) -> float:
    return SequenceMatcher(None, normalize_whitespace(left), normalize_whitespace(right)).ratio()


def build_cluster_key(title: str) -> str:
    tokens = [token for token in normalize_key(title).split("-") if token]
    return "-".join(tokens[:8])


def split_into_chunks(text: str | None, max_chars: int = 400) -> list[str]:
    cleaned = normalize_whitespace(text)
    if not cleaned:
        return []

    chunks: list[str] = []
    current = []
    current_size = 0
    for sentence in re.split(r"(?<=[.!?])\s+", cleaned):
        sentence = sentence.strip()
        if not sentence:
            continue
        projected = current_size + len(sentence) + 1
        if current and projected > max_chars:
            chunks.append(" ".join(current))
            current = [sentence]
            current_size = len(sentence)
        else:
            current.append(sentence)
            current_size = projected
    if current:
        chunks.append(" ".join(current))
    return chunks
