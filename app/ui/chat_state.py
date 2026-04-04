from __future__ import annotations


def append_chat_message(
    messages: list[dict],
    role: str,
    content: str,
    meta: str | None = None,
) -> list[dict]:
    messages.append({"role": role, "content": content, "meta": meta})
    return messages


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
