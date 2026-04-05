from __future__ import annotations

from datetime import datetime


def build_chat_timestamp(value: datetime | None = None) -> str:
    instant = value or datetime.now()
    return instant.strftime("%H:%M")


DEFAULT_CHAT_MESSAGES = [
    {
        "role": "assistant",
        "content": (
            "Xin chào. Bạn có thể hỏi tự nhiên về tin hot, giá vàng, tỷ giá, thời tiết, "
            "chính sách và giao thông. Nếu chưa biết bắt đầu từ đâu, "
            "hãy bấm một gợi ý ngay phía trên."
        ),
        "meta": "Chat local qua API /chat/query",
        "timestamp": build_chat_timestamp(),
        "items": [],
    }
]


def build_default_chat_messages() -> list[dict]:
    return [
        {
            **message,
            "items": list(message.get("items", [])),
        }
        for message in DEFAULT_CHAT_MESSAGES
    ]


def reset_chat_messages(messages: list[dict] | None = None) -> list[dict]:
    default_messages = build_default_chat_messages()
    if messages is None:
        return default_messages
    messages.clear()
    messages.extend(default_messages)
    return messages


def append_chat_message(
    messages: list[dict],
    role: str,
    content: str,
    meta: str | None = None,
    timestamp: str | None = None,
    intent: str | None = None,
    follow_ups: list[str] | None = None,
    items: list[dict] | None = None,
) -> list[dict]:
    messages.append(
        {
            "role": role,
            "content": content,
            "meta": meta,
            "timestamp": timestamp or build_chat_timestamp(),
            "intent": intent,
            "follow_ups": list(follow_ups or []),
            "items": list(items or []),
        }
    )
    return messages


def build_chat_request(
    question: str,
    *,
    mode: str = "default",
    context_item: dict | None = None,
) -> dict:
    return {
        "question": question.strip(),
        "mode": mode,
        "context_item": dict(context_item or {}) or None,
    }


def ensure_pending_user_visible(messages: list[dict], question: str) -> list[dict]:
    clean_question = question.strip()
    if not clean_question:
        return messages

    if messages:
        last_message = messages[-1]
        if (
            last_message.get("role") == "user"
            and last_message.get("content", "").strip() == clean_question
        ):
            return messages

    return append_chat_message(messages, "user", clean_question)


def build_chat_meta(answer_payload: dict) -> str:
    meta_parts = [
        f"Intent: {answer_payload.get('intent', 'unknown')}",
        f"Tool: {answer_payload.get('tool_called', 'none')}",
    ]
    if answer_payload.get("sources"):
        meta_parts.append("Nguồn: " + ", ".join(answer_payload["sources"]))
    if answer_payload.get("updated_at"):
        meta_parts.append("Cập nhật: " + str(answer_payload["updated_at"]))
    return " | ".join(meta_parts)


def extract_recent_user_questions(messages: list[dict], limit: int = 3) -> list[str]:
    recent_questions: list[str] = []
    seen: set[str] = set()
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = str(message.get("content", "")).strip()
        if not content or content in seen:
            continue
        recent_questions.append(content)
        seen.add(content)
        if len(recent_questions) >= limit:
            break
    return recent_questions
