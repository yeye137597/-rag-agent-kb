from fastapi import APIRouter

from backend.core.deps import AdminUser
from backend.schemas.models import ModelConfigResponse, ModelConfigUpdate
from src.auth import write_audit_log
from src.model_factory import get_current_model_config, update_env_config


router = APIRouter()


@router.get("/config", response_model=ModelConfigResponse)
def get_model_config(current_user: AdminUser) -> ModelConfigResponse:
    return ModelConfigResponse(**get_current_model_config())


@router.post("/config", response_model=ModelConfigResponse)
def update_model_config(payload: ModelConfigUpdate, current_user: AdminUser) -> ModelConfigResponse:
    values: dict[str, str] = {}
    audit_parts = []

    if payload.llm:
        if payload.llm.provider is not None:
            values["LLM_PROVIDER"] = payload.llm.provider
        if payload.llm.base_url is not None:
            values["LLM_BASE_URL"] = payload.llm.base_url
        if payload.llm.model is not None:
            values["LLM_MODEL"] = payload.llm.model
            audit_parts.append(f"LLM model={payload.llm.model}")
        if payload.llm.temperature is not None:
            values["LLM_TEMPERATURE"] = str(payload.llm.temperature)
        if payload.llm.api_key:
            values["LLM_API_KEY"] = payload.llm.api_key
            audit_parts.append("LLM API key updated")

    if payload.embedding:
        if payload.embedding.provider is not None:
            values["EMBEDDING_PROVIDER"] = payload.embedding.provider
        if payload.embedding.model is not None:
            values["EMBEDDING_MODEL"] = payload.embedding.model
            audit_parts.append(f"Embedding model={payload.embedding.model}")
        if payload.embedding.device is not None:
            values["EMBEDDING_DEVICE"] = payload.embedding.device

    if values:
        update_env_config(values)
        write_audit_log(
            current_user["username"],
            "管理员修改模型配置",
            "; ".join(audit_parts) or "model config updated",
        )

    return ModelConfigResponse(**get_current_model_config())
