from __future__ import annotations

from pathlib import Path

import pytest

from app.core.settings import get_settings
from app.services.retention_config import (
    CleanupRetentionPolicy,
    _load_cleanup_retention_policy_from_file,
    load_cleanup_retention_policy,
)


def test_load_cleanup_retention_policy_from_file_reads_config(tmp_path: Path) -> None:
    config_path = tmp_path / "retention.yml"
    config_path.write_text(
        """
cleanup:
  articles_days: 45
  traffic_events_days: 10
  raw_documents_days: 7
  crawl_jobs_days: 21
""".strip(),
        encoding="utf-8",
    )

    policy = _load_cleanup_retention_policy_from_file(config_path)

    assert policy == CleanupRetentionPolicy(
        articles_days=45,
        traffic_events_days=10,
        raw_documents_days=7,
        crawl_jobs_days=21,
    )


def test_load_cleanup_retention_policy_uses_settings_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "retention.yml"
    config_path.write_text(
        """
cleanup:
  articles_days: 60
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("RETENTION_CONFIG_PATH", str(config_path))
    get_settings.cache_clear()
    load_cleanup_retention_policy.cache_clear()

    policy = load_cleanup_retention_policy()

    assert policy.articles_days == 60
    assert policy.traffic_events_days == 14

    load_cleanup_retention_policy.cache_clear()
    get_settings.cache_clear()
