from __future__ import annotations

from datetime import datetime

from app.models import PolicyDocument, Source
from app.repositories.policy_repository import PolicyRepository
from app.services.policy_service import PolicyService


def _create_policy_source(db) -> Source:
    source = Source(
        pipeline_name="policy",
        source_name="congbao_policy_updates_live",
        source_type="html",
        category_default="chinh_sach",
        base_url="https://example.com/policy",
        config_json={},
    )
    db.add(source)
    db.flush()
    return source


def test_policy_search_prefers_recent_documents_but_keeps_older_match(db_session_factory) -> None:
    repo = PolicyRepository()
    with db_session_factory() as db:
        source = _create_policy_source(db)
        old_row = PolicyDocument(
            source_id=source.id,
            title="Hướng dẫn học đường và an toàn trường học",
            summary="Văn bản cũ nhưng vẫn liên quan đến giáo dục học đường.",
            content_clean="Nội dung giáo dục học đường cho năm cũ.",
            field="giáo dục",
            issuing_agency="Bộ Giáo dục và Đào tạo",
            doc_number="11/2024/TT-BGDDT",
            issued_at=datetime(2024, 1, 10, 9, 0, 0),
            effective_at=datetime(2024, 2, 1, 0, 0, 0),
            canonical_url="https://example.com/policy/old-school",
        )
        recent_row = PolicyDocument(
            source_id=source.id,
            title="Hướng dẫn mới về học đường và tuyển sinh đầu cấp",
            summary="Văn bản mới về giáo dục học đường.",
            content_clean="Nội dung mới nhất cho tuyển sinh và học đường.",
            field="giáo dục",
            issuing_agency="Bộ Giáo dục và Đào tạo",
            doc_number="08/2026/TT-BGDDT",
            issued_at=datetime(2026, 3, 28, 9, 0, 0),
            effective_at=datetime(2026, 4, 15, 0, 0, 0),
            canonical_url="https://example.com/policy/recent-school",
        )
        db.add_all([old_row, recent_row])
        db.commit()

        rows = repo.search(
            db,
            query="học đường",
            limit=5,
            reference_now=datetime(2026, 4, 4, 12, 0, 0),
        )

    assert len(rows) == 2
    assert rows[0].title == "Hướng dẫn mới về học đường và tuyển sinh đầu cấp"
    assert {row.canonical_url for row in rows} == {
        "https://example.com/policy/recent-school",
        "https://example.com/policy/old-school",
    }


def test_policy_service_skips_demo_rows_when_live_rows_exist(db_session_factory) -> None:
    with db_session_factory() as db:
        live_source = Source(
            pipeline_name="policy",
            source_name="congbao_policy_updates_live",
            source_type="html",
            category_default="chinh_sach",
            base_url="https://example.com/live-policy",
            config_json={},
        )
        demo_source = Source(
            pipeline_name="policy",
            source_name="chinhphu_policy_updates",
            source_type="json",
            category_default="chinh_sach",
            base_url="https://example.com/demo-policy",
            config_json={"demo_only_source": True},
        )
        db.add_all([live_source, demo_source])
        db.flush()

        db.add_all(
            [
                PolicyDocument(
                    source_id=live_source.id,
                    title="Thông tư mới về giáo dục học đường",
                    summary="Văn bản live về giáo dục học đường.",
                    content_clean="Nội dung live cho học đường và trường học.",
                    field="giáo dục",
                    issuing_agency="Bộ Giáo dục và Đào tạo",
                    doc_number="12/2026/TT-BGDDT",
                    issued_at=datetime(2026, 4, 2, 9, 0, 0),
                    effective_at=datetime(2026, 4, 20, 0, 0, 0),
                    canonical_url="https://example.com/live-school",
                ),
                PolicyDocument(
                    source_id=demo_source.id,
                    title="Hướng dẫn demo về giáo dục học đường",
                    summary="Bản ghi demo cũ cho học đường.",
                    content_clean="Nội dung demo học đường.",
                    field="giáo dục",
                    issuing_agency="Bộ Giáo dục và Đào tạo",
                    doc_number="02/2026/TT-BGDDT",
                    issued_at=datetime(2026, 4, 3, 9, 0, 0),
                    effective_at=datetime(2026, 4, 10, 0, 0, 0),
                    canonical_url="https://example.com/demo-school",
                ),
            ]
        )
        db.commit()

        payload = PolicyService(db).search_policy(query="học đường", limit=10)

    assert payload["items"]
    assert {item["source"] for item in payload["items"]} == {"congbao_policy_updates_live"}
