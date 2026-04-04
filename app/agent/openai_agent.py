from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.agent.fallback_agent import FallbackAgent
from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.tool_registry import ToolRegistry
from app.core.logging import get_logger
from app.core.settings import get_settings

logger = get_logger(__name__)


class OpenAIAgent:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.registry = ToolRegistry(db)
        self.fallback = FallbackAgent(db)

    def is_available(self) -> bool:
        return bool(self.settings.chat_use_openai and self.settings.openai_api_key)

    def answer(self, question: str) -> dict:
        if not self.is_available():
            return self.fallback.answer(question)

        try:
            from openai import OpenAI
        except ImportError:
            return self.fallback.answer(question)

        client = OpenAI(api_key=self.settings.openai_api_key)
        input_messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        tools = self.registry.definitions()

        tool_name = "none"
        last_payload: dict[str, Any] = {}
        try:
            response = client.responses.create(
                model=self.settings.openai_model,
                input=input_messages,
                tools=tools,
            )
            for _ in range(3):
                tool_calls = [item for item in response.output if item.type == "function_call"]
                if not tool_calls:
                    break

                tool_outputs: list[dict[str, Any]] = []
                for tool_call in tool_calls:
                    tool_name = tool_call.name
                    arguments = json.loads(tool_call.arguments or "{}")
                    last_payload = self.registry.call(tool_call.name, arguments)
                    tool_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": tool_call.call_id,
                            "output": json.dumps(last_payload, default=str, ensure_ascii=False),
                        }
                    )

                response = client.responses.create(
                    model=self.settings.openai_model,
                    previous_response_id=response.id,
                    input=tool_outputs,
                    tools=tools,
                )
        except Exception as exc:
            logger.warning("Goi OpenAI that bai, fallback sang agent noi bo: %s", exc)
            return self.fallback.answer(question)

        answer_text = getattr(response, "output_text", None)
        if not answer_text:
            answer_text = self.fallback.answer(question)["answer"]
        return {
            "question": question,
            "intent": "openai_tool_calling",
            "tool_called": tool_name,
            "answer": answer_text,
            "sources": self.fallback._extract_sources(last_payload),
            "updated_at": last_payload.get("updated_at")
            if isinstance(last_payload, dict)
            else None,
            "data": last_payload,
        }
