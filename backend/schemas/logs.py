from typing import Any

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    username: str | None = None
    action: str | None = None
    detail: str | None = None
    created_at: str | None = None


class QueryLogItem(BaseModel):
    time: str | None = None
    username: str | None = None
    role: str | None = None
    question: str | None = None
    answer: str | None = None
    selected_kbs: list[dict[str, Any]] = []
    rewritten_question: str | None = None
    retrieved_docs: list[dict[str, Any]] = []
    latency: float | None = None
    retry_count: int | None = None
    evaluation_reason: str | None = None
