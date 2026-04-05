from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import APIModel


class ChatResponseItem(APIModel):
    kind: str
    title: str
    source: str | None = None
    url: str | None = None
    internal_id: int | None = None
    summary: str | None = None
    updated_at: datetime | None = None
    action_type: str = "detail"
    dataset_title: str | None = None
    explorer_keyword: str | None = None
    explorer_filters: dict[str, str] = Field(default_factory=dict)
    question_hint: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class ChatQueryRequest(APIModel):
    question: str = Field(min_length=3)
    mode: Literal["default", "summarize_item", "ask_about_item"] = "default"
    context_item: ChatResponseItem | None = None


class ChatQueryResponse(APIModel):
    question: str
    intent: str
    tool_called: str
    answer: str
    sources: list[str]
    updated_at: datetime | None = None
    data: dict | None = None
    items: list[ChatResponseItem] = Field(default_factory=list)
