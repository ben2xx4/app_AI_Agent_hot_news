from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from app.agent.openai_agent import OpenAIAgent
from app.services.chat_presenter import build_context_chat_response, enrich_chat_response


class ChatService:
    def __init__(self, db: Session) -> None:
        self.agent = OpenAIAgent(db)

    def answer_question(
        self,
        question: str,
        *,
        mode: str = "default",
        context_item: Mapping[str, Any] | None = None,
    ) -> dict:
        if mode != "default" and context_item:
            return build_context_chat_response(
                question=question,
                mode=mode,
                context_item=context_item,
            )
        return enrich_chat_response(self.agent.answer(question))
