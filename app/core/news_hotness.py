from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from html import unescape
from typing import Any

from app.core.text import fold_text

HARD_NEWS_KEYWORDS = (
    "chinh phu",
    "thu tuong",
    "quoc hoi",
    "thanh uy",
    "bo truong",
    "nghi dinh",
    "nghi quyet",
    "du thao",
    "luat",
    "dieu tra",
    "khoi to",
    "bat giu",
    "toa an",
    "thuong mai",
    "ngan hang",
    "tai chinh",
    "kinh te",
    "thi truong",
    "gia vang",
    "ty gia",
    "gia xang",
    "dau tu",
    "xuat khau",
    "giao thong",
    "thong xe",
    "phan luong",
    "cam duong",
    "un tac",
    "tai nan",
    "bao",
    "lu",
    "dong dat",
    "bien dong",
)

SOFT_NEWS_KEYWORDS = (
    "loi ich",
    "song khoe",
    "suc khoe",
    "hat lanh",
    "tap luyen",
    "bi quyet",
    "meo",
    "gen z",
    "claude monet",
    "tranh",
    "nghe thuat",
    "am anh",
    "showbiz",
    "nguoi mau",
    "hoa hau",
    "du lich",
    "tinh yeu",
    "huong dan",
)


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _score_source_name(source_name: str) -> int:
    folded = fold_text(source_name)
    if folded.endswith("thoi su"):
        return 8
    if "tin moi" in folded or "trang chu" in folded:
        return 5
    if "kinh doanh" in folded or "kinh te" in folded:
        return 4
    if "the gioi" in folded:
        return 2
    if "giao duc" in folded:
        return 1
    if "the thao" in folded:
        return -2
    return 0


def _score_category(category: str | None) -> int:
    folded = fold_text(category)
    if folded == "thoi su":
        return 7
    if folded == "tin tuc":
        return 5
    if folded in {"kinh doanh", "kinh te"}:
        return 4
    if folded == "the gioi":
        return 2
    if folded == "giao duc":
        return 1
    if folded == "the thao":
        return -2
    return 0


def _score_recency(published_at: datetime | None, *, now: datetime) -> int:
    if published_at is None:
        return 0
    age_hours = max((now - published_at).total_seconds() / 3600, 0)
    if age_hours <= 6:
        return 8
    if age_hours <= 12:
        return 6
    if age_hours <= 24:
        return 4
    if age_hours <= 48:
        return 2
    return 0


def score_hot_news_candidate(
    *,
    title: str | None,
    summary: str | None,
    category: str | None,
    source_name: str,
    published_at: datetime | None,
    now: datetime | None = None,
) -> int:
    reference_now = now or _utcnow_naive()
    folded_title = fold_text(unescape(title) if title else title)
    folded_summary = fold_text(unescape(summary) if summary else summary)
    combined_text = f"{folded_title} {folded_summary}".strip()

    score = 0
    score += _score_source_name(source_name)
    score += _score_category(category)
    score += _score_recency(published_at, now=reference_now)

    for keyword in HARD_NEWS_KEYWORDS:
        if keyword in combined_text:
            score += 3

    soft_hits = 0
    for keyword in SOFT_NEWS_KEYWORDS:
        if keyword in combined_text:
            soft_hits += 1
            score -= 5

    if folded_title.endswith("?"):
        score -= 1

    if soft_hits and score < 8:
        score -= 4

    return score


def rank_hot_news_rows(
    rows: Iterable[Any],
    *,
    source_name_map: dict[int, str],
    limit: int,
    now: datetime | None = None,
) -> list[Any]:
    reference_now = now or _utcnow_naive()
    scored_rows: list[tuple[int, Any]] = []
    for row in rows:
        if getattr(row, "duplicate_status", None) == "exact_duplicate":
            continue
        source_name = source_name_map.get(getattr(row, "source_id", None) or -1, "unknown")
        score = score_hot_news_candidate(
            title=getattr(row, "title", None),
            summary=getattr(row, "summary", None),
            category=getattr(row, "category", None),
            source_name=source_name,
            published_at=getattr(row, "published_at", None),
            now=reference_now,
        )
        scored_rows.append((score, row))

    scored_rows.sort(
        key=lambda item: (
            item[0],
            getattr(item[1], "published_at", None) or datetime.min,
            getattr(item[1], "id", 0),
        ),
        reverse=True,
    )

    selected: list[Any] = []
    selected_ids: set[int] = set()
    source_counts: Counter[str] = Counter()
    max_per_source = 2 if limit >= 5 else 1

    for _, row in scored_rows:
        row_id = getattr(row, "id", None)
        if row_id is not None and row_id in selected_ids:
            continue
        source_name = source_name_map.get(getattr(row, "source_id", None) or -1, "unknown")
        if source_counts[source_name] >= max_per_source:
            continue
        selected.append(row)
        if row_id is not None:
            selected_ids.add(row_id)
        source_counts[source_name] += 1
        if len(selected) >= limit:
            return selected

    for _, row in scored_rows:
        row_id = getattr(row, "id", None)
        if row_id is not None and row_id in selected_ids:
            continue
        selected.append(row)
        if row_id is not None:
            selected_ids.add(row_id)
        if len(selected) >= limit:
            break
    return selected
