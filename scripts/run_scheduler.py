from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import _bootstrap  # noqa: F401

from app.core.logging import get_logger
from app.db.session import ensure_sqlite_schema
from app.services.scheduler_service import SchedulerService

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scheduler don gian cho pipeline")
    parser.add_argument("--demo-only", action="store_true")
    parser.add_argument("--tick-seconds", type=int, default=30)
    parser.add_argument("--run-once", action="store_true")
    parser.add_argument("--show-status", action="store_true")
    parser.add_argument(
        "--pipeline",
        action="append",
        choices=["news", "price", "weather", "policy", "traffic"],
    )
    parser.add_argument("--source", action="append", dest="source_names")
    parser.add_argument(
        "--status-file",
        default="data/processed/scheduler_status.json",
        help="Noi luu trang thai scheduler local",
    )
    args = parser.parse_args()

    ensure_sqlite_schema()
    service = SchedulerService(
        demo_only=args.demo_only,
        pipeline_names=set(args.pipeline or []),
        source_names=set(args.source_names or []),
        status_path=Path(args.status_file),
    )

    if args.show_status:
        print(json.dumps({"jobs": service.dump_status()}, ensure_ascii=False, indent=2))
        return

    while True:
        logger.info("Bat dau vong scheduler")
        results = service.run_due_jobs()
        print(
            json.dumps(
                {"runs": results, "jobs": service.dump_status()},
                ensure_ascii=False,
                indent=2,
            )
        )

        if args.run_once:
            break
        time.sleep(args.tick_seconds)


if __name__ == "__main__":
    main()
