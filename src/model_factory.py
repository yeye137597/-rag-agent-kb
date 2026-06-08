import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from config import BASE_DIR


ENV_FILE = BASE_DIR / ".env"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_llm_api_key() -> str:
    return _env("LLM_API_KEY") or _env("DEEPSEEK_API_KEY")


def has_llm_api_key() -> bool:
    return bool(get_llm_api_key())


def get_llm_provider() -> str:
    return _env("LLM_PROVIDER", "deepseek")


def get_llm_base_url() -> str:
    return _env("LLM_BASE_URL") or _env("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


def get_llm_model() -> str:
    return _env("LLM_MODEL") or _env("DEEPSEEK_MODEL", "deepseek-chat")


def get_llm_temperature() -> float:
    raw_value = _env("LLM_TEMPERATURE", "0.2")
    try:
        return float(raw_value)
    except ValueError:
        return 0.2


def get_embedding_provider() -> str:
    return _env("EMBEDDING_PROVIDER", "huggingface")


def get_embedding_model_name() -> str:
    return _env("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")


def get_embedding_device() -> str:
    return _env("EMBEDDING_DEVICE", "cpu")


def get_chat_model(temperature: float | None = None) -> ChatOpenAI:
    api_key = get_llm_api_key()
    if not api_key:
        raise ValueError("未配置 LLM_API_KEY。兼容旧配置时也可以使用 DEEPSEEK_API_KEY。")

    provider = get_llm_provider()
    if provider not in {"deepseek", "openai_compatible"}:
        raise ValueError(f"不支持的 LLM_PROVIDER: {provider}")

    return ChatOpenAI(
        api_key=api_key,
        base_url=get_llm_base_url(),
        model=get_llm_model(),
        temperature=get_llm_temperature() if temperature is None else temperature,
    )


def get_embedding_model() -> HuggingFaceEmbeddings:
    provider = get_embedding_provider()
    if provider != "huggingface":
        raise ValueError(f"不支持的 EMBEDDING_PROVIDER: {provider}")

    return HuggingFaceEmbeddings(
        model_name=get_embedding_model_name(),
        model_kwargs={"device": get_embedding_device()},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_current_embedding_config() -> dict:
    return {
        "provider": get_embedding_provider(),
        "model": get_embedding_model_name(),
        "device": get_embedding_device(),
    }


def get_current_model_config() -> dict:
    return {
        "llm": {
            "provider": get_llm_provider(),
            "base_url": get_llm_base_url(),
            "model": get_llm_model(),
            "temperature": get_llm_temperature(),
            "api_key_configured": has_llm_api_key(),
        },
        "embedding": get_current_embedding_config(),
    }


def is_same_embedding_config(kb_embedding: dict | None, current_embedding: dict | None = None) -> bool:
    if not kb_embedding:
        return False
    current_embedding = current_embedding or get_current_embedding_config()
    return (
        kb_embedding.get("provider") == current_embedding.get("provider")
        and kb_embedding.get("model") == current_embedding.get("model")
    )


def update_env_config(values: dict[str, str]) -> None:
    existing = _read_env_file(ENV_FILE)
    existing.update({key: value for key, value in values.items() if value is not None})
    _write_env_file(ENV_FILE, existing)
    for key, value in existing.items():
        os.environ[key] = value
    load_dotenv(ENV_FILE, override=True)


def _read_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _write_env_file(path: Path, values: dict[str, str]) -> None:
    ordered_keys = [
        "LLM_PROVIDER",
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "LLM_MODEL",
        "LLM_TEMPERATURE",
        "EMBEDDING_PROVIDER",
        "EMBEDDING_MODEL",
        "EMBEDDING_DEVICE",
        "JWT_SECRET_KEY",
    ]
    lines = []
    written = set()
    for key in ordered_keys:
        if key in values:
            lines.append(f"{key}={values[key]}")
            written.add(key)
    for key in sorted(values):
        if key not in written:
            lines.append(f"{key}={values[key]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
