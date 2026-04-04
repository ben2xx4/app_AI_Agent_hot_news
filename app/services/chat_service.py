from __future__ import annotations

from sqlalchemy.orm import Session

from app.agent.openai_agent import OpenAIAgent


class ChatService:
    def __init__(self, db: Session) -> None:
        self.agent = OpenAIAgent(db)

    def answer_question(self, question: str) -> dict:
        return self.agent.answer(question)
