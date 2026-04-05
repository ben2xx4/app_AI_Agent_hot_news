from __future__ import annotations

from app.ui.data_browser import (
    list_dataset_definitions,
    load_core_dataset_overview,
    load_dataset_preview,
)


def test_data_browser_lists_main_datasets() -> None:
    datasets = list_dataset_definitions(include_technical=False)
    dataset_keys = {dataset.key for dataset in datasets}

    assert "articles" in dataset_keys
    assert "price_snapshots" in dataset_keys
    assert "weather_snapshots" in dataset_keys
    assert "policy_documents" in dataset_keys
    assert "traffic_events" in dataset_keys
    assert "crawl_jobs" not in dataset_keys


def test_data_browser_articles_preview_contains_source_name(seeded_db) -> None:
    with seeded_db() as db:
        payload = load_dataset_preview("articles", limit=10, db=db)

    assert payload["title"] == "Tin tức"
    assert payload["total_rows"] >= 1
    assert payload["records"]
    assert "source_name" in payload["records"][0]
    assert payload["records"][0]["title"]


def test_data_browser_price_preview_filters_by_keyword(seeded_db) -> None:
    with seeded_db() as db:
        payload = load_dataset_preview("price_snapshots", limit=20, keyword="usd", db=db)

    assert payload["matched_rows"] >= 1
    assert payload["records"]
    assert any("usd" in str(record.get("item_name", "")).lower() for record in payload["records"])


def test_core_dataset_overview_reports_main_counts(seeded_db) -> None:
    with seeded_db() as db:
        payload = load_core_dataset_overview(db=db)

    overview_map = {row["key"]: row for row in payload}
    assert overview_map["articles"]["total_rows"] >= 1
    assert overview_map["policy_documents"]["title"] == "Chính sách"
    assert overview_map["traffic_events"]["total_rows"] >= 1


def test_data_browser_price_preview_filters_by_item_name(seeded_db) -> None:
    with seeded_db() as db:
        payload = load_dataset_preview(
            "price_snapshots",
            limit=20,
            structured_filters={"item_name": "ty-gia-usd-ban-ra"},
            db=db,
        )

    assert payload["records"]
    assert all(record["item_name"] == "ty-gia-usd-ban-ra" for record in payload["records"])


def test_data_browser_weather_preview_filters_by_location(seeded_db) -> None:
    with seeded_db() as db:
        payload = load_dataset_preview(
            "weather_snapshots",
            limit=20,
            structured_filters={"location": "Hà Nội"},
            db=db,
        )

    assert payload["records"]
    assert all(record["location"] == "Hà Nội" for record in payload["records"])


def test_data_browser_articles_preview_filters_by_pipeline_and_source(seeded_db) -> None:
    with seeded_db() as db:
        payload = load_dataset_preview(
            "articles",
            limit=20,
            structured_filters={
                "pipeline_name": "news",
                "source_name": "vnexpress_rss_tin_moi",
            },
            db=db,
        )

    assert payload["records"]
    assert all(record["pipeline_name"] == "news" for record in payload["records"])
    assert all(record["source_name"] == "vnexpress_rss_tin_moi" for record in payload["records"])


def test_data_browser_sort_mode_oldest_reverses_article_order(seeded_db) -> None:
    with seeded_db() as db:
        newest_payload = load_dataset_preview("articles", limit=10, sort_mode="latest", db=db)
        oldest_payload = load_dataset_preview("articles", limit=10, sort_mode="oldest", db=db)

    assert newest_payload["records"]
    assert oldest_payload["records"]
    assert (
        newest_payload["records"][0]["published_at"]
        >= oldest_payload["records"][0]["published_at"]
    )
