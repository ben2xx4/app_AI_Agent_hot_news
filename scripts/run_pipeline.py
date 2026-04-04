from __future__ import annotations

import argparse
import json
from dataclasses import asdict

import _bootstrap  # noqa: F401

from app.db.session import ensure_sqlite_schema
from app.pipelines.news.pipeline import NewsPipeline
from app.pipelines.policy.pipeline import PolicyPipeline
from app.pipelines.price.pipeline import PricePipeline
from app.pipelines.traffic.pipeline import TrafficPipeline
from app.pipelines.weather.pipeline import WeatherPipeline

PIPELINES = {
    "news": NewsPipeline,
    "price": PricePipeline,
    "weather": WeatherPipeline,
    "policy": PolicyPipeline,
    "traffic": TrafficPipeline,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Chay pipeline ingestion")
    parser.add_argument("--pipeline", choices=["all", *PIPELINES.keys()], required=True)
    parser.add_argument("--demo-only", action="store_true", help="Chi dung fixture demo")
    parser.add_argument(
        "--source",
        action="append",
        dest="source_names",
        help="Chi chay mot source cu the. Co the lap lai tham so nay.",
    )
    args = parser.parse_args()

    ensure_sqlite_schema()

    pipeline_names = list(PIPELINES.keys()) if args.pipeline == "all" else [args.pipeline]
    summaries = []
    source_names = set(args.source_names or [])
    for pipeline_name in pipeline_names:
        pipeline = PIPELINES[pipeline_name](
            demo_only=args.demo_only,
            source_names=source_names or None,
        )
        summaries.extend(asdict(summary) for summary in pipeline.run())

    print(json.dumps({"summaries": summaries}, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
