from __future__ import annotations

import argparse
import json
from dataclasses import asdict

try:
    import _bootstrap  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    from scripts import _bootstrap  # type: ignore  # noqa: F401

from app.db.session import ensure_sqlite_schema
from app.pipelines.price.pipeline import PricePipeline


def refresh_live_prices(*, source_names: set[str] | None = None) -> list[dict]:
    ensure_sqlite_schema()
    pipeline = PricePipeline(demo_only=False, source_names=source_names or None)
    return [asdict(summary) for summary in pipeline.run()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lam moi du lieu gia live ma khong chay lai seed demo"
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="source_names",
        help="Chi lam moi mot source gia cu the. Co the lap lai tham so nay.",
    )
    args = parser.parse_args()

    summaries = refresh_live_prices(source_names=set(args.source_names or []))
    print(json.dumps({"summaries": summaries}, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
