from __future__ import annotations

from datetime import UTC, datetime

from app.pipelines.common.processing import (
    is_datetime_within_age_window,
    parse_datetime,
    resolve_max_age_days,
)


def test_parse_datetime_supports_rfc822_pubdate() -> None:
    parsed = parse_datetime("Fri, 04 Apr 2026 07:45:00 GMT")

    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.month == 4
    assert parsed.day == 4
    assert parsed.tzinfo is not None


def test_resolve_max_age_days_ignores_invalid_values() -> None:
    assert resolve_max_age_days(None) is None
    assert resolve_max_age_days("") is None
    assert resolve_max_age_days("abc") is None
    assert resolve_max_age_days(0) is None


def test_is_datetime_within_age_window_accepts_recent_timestamp() -> None:
    now = datetime(2026, 4, 4, 12, 0, 0, tzinfo=UTC)
    candidate = datetime(2026, 3, 29, 8, 30, 0, tzinfo=UTC)

    assert is_datetime_within_age_window(candidate, 14, now_provider=lambda: now) is True


def test_is_datetime_within_age_window_rejects_old_timestamp() -> None:
    now = datetime(2026, 4, 4, 12, 0, 0, tzinfo=UTC)
    candidate = datetime(2026, 3, 10, 8, 30, 0, tzinfo=UTC)

    assert is_datetime_within_age_window(candidate, 14, now_provider=lambda: now) is False
