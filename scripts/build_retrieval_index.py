from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401

from app.db.session import ensure_sqlite_schema, session_scope
from app.services.retrieval_index_service import RetrievalIndexService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build lai experimental retrieval index cho news va policy"
    )
    parser.add_argument(
        "--doc-type",
        choices=["all", "news", "policy"],
        default="all",
        help="Loai tai lieu can build index",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Gioi han so ban ghi can reindex cho moi nhom",
    )
    args = parser.parse_args()

    ensure_sqlite_schema()

    with session_scope() as db:
        service = RetrievalIndexService(db)
        results: list[dict[str, int | str]] = []
        if args.doc_type in {"all", "news"}:
            results.append(service.reindex_articles(limit=args.limit))
        if args.doc_type in {"all", "policy"}:
            results.append(service.reindex_policies(limit=args.limit))

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
