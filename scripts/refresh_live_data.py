from __future__ import annotations

import argparse
import json
from dataclasses import asdict

try:
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    from scripts import _bootstrap  # type: ignore  # noqa: F401

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


def refresh_live_data(
    *,
    pipeline_names: list[str] | None = None,
    source_names: set[str] | None = None,
) -> list[dict]:
    ensure_sqlite_schema()
    requested_names = pipeline_names or list(PIPELINES.keys())
    normalized_names = list(dict.fromkeys(requested_names))
    summaries: list[dict] = []

    for pipeline_name in normalized_names:
        if pipeline_name not in PIPELINES:
            raise ValueError(f"Khong ho tro pipeline: {pipeline_name}")
        pipeline = PIPELINES[pipeline_name](
            demo_only=False,
            source_names=source_names or None,
        )
        summaries.extend(asdict(summary) for summary in pipeline.run())
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lam moi du lieu live cho nhieu pipeline ma khong chay lai seed demo"
    )
    parser.add_argument(
        "--pipeline",
        action="append",
        choices=list(PIPELINES.keys()),
        dest="pipeline_names",
        help="Chi lam moi mot pipeline cu the. Co the lap lai tham so nay.",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="source_names",
        help="Chi lam moi mot source cu the. Co the lap lai tham so nay.",
    )
    args = parser.parse_args()

    summaries = refresh_live_data(
        pipeline_names=args.pipeline_names,
        source_names=set(args.source_names or []),
    )
    print(json.dumps({"summaries": summaries}, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
