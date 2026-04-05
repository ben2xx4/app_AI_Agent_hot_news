from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import _bootstrap  # noqa: F401

from app.core.logging import get_logger
from app.db.session import ensure_sqlite_schema, session_scope
from app.services.cleanup_service import CleanupService
from app.services.retention_config import load_cleanup_retention_policy
from app.services.scheduler_service import SchedulerService

logger = get_logger(__name__)


def main() -> None:
    retention = load_cleanup_retention_policy()
    parser = argparse.ArgumentParser(description="Scheduler don gian cho pipeline")
    parser.add_argument("--demo-only", action="store_true")
    parser.add_argument("--tick-seconds", type=int, default=30)
    parser.add_argument("--run-once", action="store_true")
    parser.add_argument("--show-status", action="store_true")
    parser.add_argument("--cleanup-after-run", action="store_true")
    parser.add_argument("--cleanup-apply", action="store_true")
    parser.add_argument("--cleanup-news-days", type=int, default=None)
    parser.add_argument("--cleanup-traffic-days", type=int, default=None)
    parser.add_argument("--cleanup-raw-days", type=int, default=None)
    parser.add_argument("--cleanup-crawl-job-days", type=int, default=None)
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
        print(
            json.dumps(
                {
                    "summary": service.dump_health_summary(),
                    "jobs": service.dump_status(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    while True:
        logger.info("Bat dau vong scheduler")
        results = service.run_due_jobs()
        cleanup_summary = None
        if args.cleanup_after_run:
            with session_scope() as db:
                cleanup_summary = CleanupService(db).run(
                    apply=args.cleanup_apply,
                    news_days=args.cleanup_news_days or retention.articles_days,
                    traffic_days=args.cleanup_traffic_days or retention.traffic_events_days,
                    raw_days=args.cleanup_raw_days or retention.raw_documents_days,
                    crawl_job_days=args.cleanup_crawl_job_days or retention.crawl_jobs_days,
                )
        print(
            json.dumps(
                {
                    "runs": results,
                    "cleanup": cleanup_summary,
                    "summary": service.dump_health_summary(),
                    "jobs": service.dump_status(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        if args.run_once:
            break
        time.sleep(args.tick_seconds)


if __name__ == "__main__":
    main()
