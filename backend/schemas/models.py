from pydantic import BaseModel


class LlmConfig(BaseModel):
    provider: str
    base_url: str
    model: str
    temperature: float
    api_key_configured: bool


class EmbeddingConfig(BaseModel):
    provider: str
    model: str
    device: str


class ModelConfigResponse(BaseModel):
    llm: LlmConfig
    embedding: EmbeddingConfig


class LlmConfigUpdate(BaseModel):
    provider: str | None = None
    base_url: str | None = None
    model: str | None = None
    temperature: float | None = None
    api_key: str | None = None


class EmbeddingConfigUpdate(BaseModel):
    provider: str | None = None
    model: str | None = None
    device: str | None = None


class ModelConfigUpdate(BaseModel):
    llm: LlmConfigUpdate | None = None
    embedding: EmbeddingConfigUpdate | None = None
