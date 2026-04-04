from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from sqlalchemy import text

from app.db.session import ensure_sqlite_schema, session_scope
from app.pipelines.news.pipeline import NewsPipeline
from app.pipelines.policy.pipeline import PolicyPipeline
from app.pipelines.price.pipeline import PricePipeline
from app.pipelines.traffic.pipeline import TrafficPipeline
from app.pipelines.weather.pipeline import WeatherPipeline

RESET_TABLES = [
    "document_embeddings",
    "traffic_events",
    "policy_documents",
    "weather_snapshots",
    "price_snapshots",
    "articles",
    "article_clusters",
    "raw_documents",
    "crawl_jobs",
    "sources",
]


def reset_demo_tables() -> None:
    with session_scope() as db:
        for table_name in RESET_TABLES:
            db.execute(text(f"DELETE FROM {table_name}"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Nap du lieu demo vao he thong")
    parser.add_argument("--demo-only", action="store_true", default=True)
    args = parser.parse_args()

    ensure_sqlite_schema()
    reset_demo_tables()

    for pipeline_cls in [
        NewsPipeline,
        PricePipeline,
        WeatherPipeline,
        PolicyPipeline,
        TrafficPipeline,
    ]:
        pipeline_cls(demo_only=args.demo_only).run()

    print("Da nap xong du lieu demo cho 5 pipeline.")


if __name__ == "__main__":
    main()
