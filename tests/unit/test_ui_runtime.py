from __future__ import annotations

from app.ui.runtime import should_load_dashboard_payloads, summarize_sidebar_runtime


def test_should_load_dashboard_payloads_only_for_dashboard() -> None:
    assert should_load_dashboard_payloads("dashboard") is True
    assert should_load_dashboard_payloads("assistant") is False
    assert should_load_dashboard_payloads("explorer") is False
    assert should_load_dashboard_payloads("system") is False


def test_summarize_sidebar_runtime_prefers_payload_sources_when_available() -> None:
    label, copy = summarize_sidebar_runtime(
        [{"key": "articles", "total_rows": 10}],
        {
            "items": [
                {"source": "vnexpress_rss_tin_moi"},
                {"source": "dantri_rss_tin_moi"},
            ]
        },
    )

    assert label == "Live"
    assert "Preview hiện nghiêng về nguồn live" in copy


def test_summarize_sidebar_runtime_falls_back_to_database_when_no_preview_payload() -> None:
    label, copy = summarize_sidebar_runtime(
        [{"key": "articles", "total_rows": 100}],
        None,
        None,
    )

    assert label == "Database local"
    assert "database hiện có" in copy
