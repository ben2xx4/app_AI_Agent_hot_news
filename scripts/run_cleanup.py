from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401

from app.db.session import ensure_sqlite_schema, session_scope
from app.services.cleanup_service import CleanupService
from app.services.retention_config import load_cleanup_retention_policy


def main() -> None:
    retention = load_cleanup_retention_policy()
    parser = argparse.ArgumentParser(description="Dọn dữ liệu cũ theo retention cục bộ")
    parser.add_argument("--apply", action="store_true", help="Xóa thật thay vì chỉ dry-run")
    parser.add_argument("--news-days", type=int, default=None)
    parser.add_argument("--traffic-days", type=int, default=None)
    parser.add_argument("--raw-days", type=int, default=None)
    parser.add_argument("--crawl-job-days", type=int, default=None)
    args = parser.parse_args()

    ensure_sqlite_schema()
    with session_scope() as db:
        payload = CleanupService(db).run(
            apply=args.apply,
            news_days=args.news_days or retention.articles_days,
            traffic_days=args.traffic_days or retention.traffic_events_days,
            raw_days=args.raw_days or retention.raw_documents_days,
            crawl_job_days=args.crawl_job_days or retention.crawl_jobs_days,
        )

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
