import os

from langchain_openai import ChatOpenAI


def has_deepseek_api_key() -> bool:
    return bool(os.getenv("DEEPSEEK_API_KEY"))


def get_llm(temperature: float = 0.2) -> ChatOpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未配置 DEEPSEEK_API_KEY，请先在 .env 中填写 DeepSeek API Key。")

    return ChatOpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=temperature,
    )

