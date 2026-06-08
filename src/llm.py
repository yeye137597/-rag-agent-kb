from langchain_openai import ChatOpenAI

from src.model_factory import get_chat_model, has_llm_api_key


def has_deepseek_api_key() -> bool:
    return has_llm_api_key()


def get_llm(temperature: float = 0.2) -> ChatOpenAI:
    return get_chat_model(temperature=temperature)
