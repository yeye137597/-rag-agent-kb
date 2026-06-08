import json

from fastapi import APIRouter, HTTPException, Query, status

from backend.core.deps import CurrentUser
from backend.schemas.logs import AuditLogItem, QueryLogItem
from config import LOG_FILE
from src.auth import list_audit_logs


router = APIRouter()


def _require_admin(user: dict) -> None:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


def _read_query_logs(username: str | None = None, limit: int = 100) -> list[dict]:
    if not LOG_FILE.exists():
        return []
    rows = []
    with LOG_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if username is None or item.get("username") == username:
                rows.append(item)
    return rows[-limit:][::-1]


@router.get("/audit", response_model=list[AuditLogItem])
def audit_logs(current_user: CurrentUser, limit: int = Query(default=100, ge=1, le=500)) -> list[AuditLogItem]:
    _require_admin(current_user)
    return [AuditLogItem(**item) for item in list_audit_logs(limit=limit)]


@router.get("/queries", response_model=list[QueryLogItem])
def query_logs(current_user: CurrentUser, limit: int = Query(default=100, ge=1, le=500)) -> list[QueryLogItem]:
    username = None if current_user["role"] == "admin" else current_user["username"]
    return [QueryLogItem(**item) for item in _read_query_logs(username=username, limit=limit)]
