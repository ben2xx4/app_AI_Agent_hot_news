from __future__ import annotations

from app.pipelines.common.processing import build_cluster_key, similarity_score, split_into_chunks


def test_processing_helpers() -> None:
    assert (
        similarity_score("Hà Nội mở thêm buýt điện", "Hà Nội đưa buýt điện mới vào khai thác")
        > 0.4
    )
    assert build_cluster_key("Hà Nội mở thêm tuyến buýt điện") == "hà-nội-mở-thêm-tuyến-buýt-điện"
    assert len(split_into_chunks("Cau 1. Cau 2. Cau 3.", max_chars=12)) >= 2
