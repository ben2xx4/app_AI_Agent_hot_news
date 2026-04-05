from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.core.content_items import build_content_item, extract_content_items, shorten_preview_text


def enrich_chat_response(response_payload: dict[str, Any]) -> dict[str, Any]:
    enriched_payload = dict(response_payload)
    data_payload = enriched_payload.get("data")
    enriched_payload["items"] = extract_content_items(
        data_payload if isinstance(data_payload, Mapping) else None
    )
    return enriched_payload


def build_context_chat_response(
    *,
    question: str,
    mode: str,
    context_item: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_item = _normalize_context_item(context_item)
    answer = _format_context_answer(normalized_item, mode=mode)
    return {
        "question": question,
        "intent": "item_summary" if mode == "summarize_item" else "item_context",
        "tool_called": "item_context",
        "answer": answer,
        "sources": [normalized_item["source"]] if normalized_item.get("source") else [],
        "updated_at": normalized_item.get("updated_at"),
        "data": {
            "mode": mode,
            "used_preview_only": not bool(
                normalized_item.get("metadata", {}).get("content_clean")
                or normalized_item.get("summary")
            ),
            "items": [normalized_item],
        },
        "items": [normalized_item],
    }


def _normalize_context_item(context_item: Mapping[str, Any]) -> dict[str, Any]:
    if context_item.get("dataset_title") and context_item.get("action_type"):
        return {
            "kind": str(context_item.get("kind") or "news"),
            "internal_id": context_item.get("internal_id"),
            "title": str(context_item.get("title") or "Mục dữ liệu"),
            "summary": context_item.get("summary"),
            "source": context_item.get("source"),
            "url": context_item.get("url"),
            "updated_at": context_item.get("updated_at"),
            "action_type": str(context_item.get("action_type") or "detail"),
            "dataset_title": context_item.get("dataset_title"),
            "explorer_keyword": context_item.get("explorer_keyword"),
            "explorer_filters": {
                str(key): str(value)
                for key, value in (context_item.get("explorer_filters") or {}).items()
                if value is not None
            },
            "question_hint": context_item.get("question_hint"),
            "metadata": {
                str(key): str(value)
                for key, value in (context_item.get("metadata") or {}).items()
                if value not in {None, ""}
            },
        }

    kind = context_item.get("kind")
    if kind:
        return build_content_item(str(kind), context_item)

    items = extract_content_items({"items": [context_item]})
    if items:
        return items[0]

    raise ValueError("Khong the chuan hoa context item cho chat")


def _format_context_answer(item: Mapping[str, Any], *, mode: str) -> str:
    title = str(item.get("title") or "Mục dữ liệu")
    summary = shorten_preview_text(
        item.get("summary") or "Hiện hệ thống mới có phần preview ngắn cho mục này.",
        limit=260,
    )
    source = item.get("source") or "không rõ nguồn"
    updated_at = item.get("updated_at") or "chưa có thời điểm"
    metadata = item.get("metadata") or {}
    kind = item.get("kind")

    if kind == "price":
        return "\n".join(
            [
                f"{title}:",
                f"- Mức hiện tại: {summary}",
                f"- Nguồn: {source}",
                f"- Cập nhật: {updated_at}",
                "- Bạn có thể hỏi tiếp về xu hướng tăng/giảm hoặc so sánh với lần cập nhật trước.",
            ]
        )

    if kind == "weather":
        warning_text = metadata.get("warning_text") or "Không có cảnh báo nổi bật."
        return "\n".join(
            [
                f"Thời tiết tại {title}:",
                f"- Tóm tắt: {summary}",
                f"- Cảnh báo: {warning_text}",
                f"- Nguồn: {source}",
                f"- Thời điểm: {updated_at}",
            ]
        )

    lines = []
    if mode == "summarize_item":
        lines.append("Tóm tắt nhanh mục đang xem:")
    else:
        lines.append("Giải thích nhanh mục đang xem:")
    lines.append(f"- Tiêu đề: {title}")
    lines.append(f"- Ý chính hiện có: {summary}")
    if metadata.get("category"):
        lines.append(f"- Nhóm nội dung: {metadata['category']}")
    if metadata.get("field"):
        lines.append(f"- Lĩnh vực: {metadata['field']}")
    if metadata.get("location"):
        lines.append(f"- Địa điểm: {metadata['location']}")
    lines.append(f"- Nguồn: {source}")
    lines.append(f"- Thời điểm: {updated_at}")

    if not item.get("url"):
        lines.append(
            "- Hệ thống hiện chưa có link gốc cho mục này, "
            "nhưng bạn vẫn có thể mở chi tiết nội bộ hoặc Explorer."
        )
    elif not item.get("summary"):
        lines.append(
            "- Hệ thống hiện chỉ có preview/metadata của mục này "
            "nên tóm tắt đang bám trên phần mô tả sẵn có, không bịa thêm nội dung."
        )
    else:
        lines.append(
            "- Nếu cần, bạn có thể mở nguồn gốc hoặc hỏi tiếp để đào sâu ý chính của mục này."
        )
    return "\n".join(lines)
