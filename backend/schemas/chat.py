from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    kb_ids: list[str]


class Source(BaseModel):
    content: str
    metadata: dict[str, Any]


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    latency: float
    retry_count: int
    is_enough: bool
    evaluation_reason: str
    rewritten_question: str
