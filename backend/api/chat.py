from fastapi import APIRouter, HTTPException, status

from backend.core.deps import CurrentUser
from backend.schemas.chat import ChatRequest, ChatResponse, Source
from config import TOP_K
from src.agent_graph import ask_question
from src.auth import get_authorized_kb_ids, write_audit_log
from src.kb_manager import get_kb_paths, list_knowledge_bases
from src.retriever import build_multi_kb_retriever


router = APIRouter()


def _select_authorized_kbs(kb_ids: list[str], user: dict) -> list[dict]:
    all_kbs = {kb["id"]: kb for kb in list_knowledge_bases()}
    missing_ids = [kb_id for kb_id in kb_ids if kb_id not in all_kbs]
    if missing_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown knowledge bases: {missing_ids}")

    if user["role"] != "admin":
        allowed_ids = get_authorized_kb_ids(user["user_id"], write_required=False)
        denied_ids = [kb_id for kb_id in kb_ids if kb_id not in allowed_ids]
        if denied_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"No access to knowledge bases: {denied_ids}")

    return [
        {"id": kb_id, "name": all_kbs[kb_id]["name"], "paths": get_kb_paths(kb_id)}
        for kb_id in kb_ids
    ]


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: CurrentUser) -> ChatResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required")
    if not payload.kb_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one knowledge base is required")

    selected_kbs = _select_authorized_kbs(payload.kb_ids, current_user)
    try:
        retriever = build_multi_kb_retriever(selected_kbs, top_k=TOP_K)
        write_audit_log(
            current_user["username"],
            "api_chat",
            f"kbs={payload.kb_ids}, question={question[:80]}",
        )
        result = ask_question(
            question,
            retriever,
            selected_kbs=selected_kbs,
            username=current_user["username"],
            role=current_user["role"],
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    sources = [
        Source(content=doc.page_content, metadata=doc.metadata or {})
        for doc in result.get("docs", [])
    ]
    return ChatResponse(
        answer=result.get("answer", ""),
        sources=sources,
        latency=float(result.get("latency", 0) or 0),
        retry_count=int(result.get("retry_count", 0) or 0),
        is_enough=bool(result.get("is_enough", False)),
        evaluation_reason=result.get("evaluation_reason", ""),
        rewritten_question=result.get("rewritten_question", question),
    )
