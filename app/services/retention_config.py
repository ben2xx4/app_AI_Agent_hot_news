from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.core.settings import get_settings


@dataclass(frozen=True)
class CleanupRetentionPolicy:
    articles_days: int = 30
    traffic_events_days: int = 14
    raw_documents_days: int = 14
    crawl_jobs_days: int = 14

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def _to_positive_int(value: object, default: int) -> int:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        return default
    return resolved if resolved > 0 else default


def _load_cleanup_retention_policy_from_file(path: Path) -> CleanupRetentionPolicy:
    if not path.exists():
        return CleanupRetentionPolicy()
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cleanup = payload.get("cleanup") or {}
    return CleanupRetentionPolicy(
        articles_days=_to_positive_int(cleanup.get("articles_days"), 30),
        traffic_events_days=_to_positive_int(cleanup.get("traffic_events_days"), 14),
        raw_documents_days=_to_positive_int(cleanup.get("raw_documents_days"), 14),
        crawl_jobs_days=_to_positive_int(cleanup.get("crawl_jobs_days"), 14),
    )


@lru_cache(maxsize=1)
def load_cleanup_retention_policy() -> CleanupRetentionPolicy:
    settings = get_settings()
    return _load_cleanup_retention_policy_from_file(Path(settings.retention_config_path))
