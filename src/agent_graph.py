import json
import time
from typing import Any, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from config import MAX_RETRY, TOP_K
from src.llm import get_llm
from src.logger import write_query_log
from src.utils import deduplicate_docs, doc_to_log_item, format_doc_source, format_docs_for_prompt


SYSTEM_PROMPT = """你是一个企业知识库问答助手。你只能根据用户提供的知识库片段回答问题，不能编造。

回答要求：
1. 如果资料中有答案，请基于资料准确回答。
2. 如果资料不足，请回答“当前知识库中没有找到足够信息。”
3. 回答要条理清晰。
4. 回答最后必须列出引用来源。
5. 引用来源必须包含知识库名称、文件名、页码、片段ID。
6. 不要使用知识库之外的信息补充答案。"""


class AgentState(TypedDict, total=False):
    question: str
    rewritten_question: str
    docs: list[Document]
    answer: str
    is_enough: bool
    retry_count: int
    evaluation_reason: str
    latency: float


def _invoke_retriever(retriever: Any, query: str) -> list[Document]:
    if hasattr(retriever, "invoke"):
        return retriever.invoke(query)
    return retriever.get_relevant_documents(query)


def retrieve_node(state: AgentState, retriever: Any) -> AgentState:
    query = state.get("rewritten_question") or state["question"]
    docs = _invoke_retriever(retriever, query)[:TOP_K]
    return {**state, "docs": deduplicate_docs(docs)}


def _parse_evaluation(content: str) -> dict:
    try:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start : end + 1]
        data = json.loads(content)
        return {
            "is_enough": bool(data.get("is_enough")),
            "reason": str(data.get("reason", "")),
            "rewrite_query": str(data.get("rewrite_query", "")),
        }
    except Exception:
        return {
            "is_enough": False,
            "reason": "LLM 评估结果不是合法 JSON，已使用兜底逻辑。",
            "rewrite_query": "",
        }


def evaluate_node(state: AgentState) -> AgentState:
    docs = state.get("docs", [])
    if not docs:
        return {
            **state,
            "is_enough": False,
            "evaluation_reason": "没有检索到相关片段。",
            "rewritten_question": state.get("rewritten_question") or state["question"],
        }

    llm = get_llm(temperature=0.0)
    prompt = f"""请判断下面的知识库片段是否足够回答用户问题。

你必须只返回 JSON，不要输出 Markdown，不要输出额外解释。

返回格式：
{{
  "is_enough": true,
  "reason": "当前资料包含用户问题需要的信息",
  "rewrite_query": ""
}}

如果不足：
{{
  "is_enough": false,
  "reason": "当前资料没有提到具体标准",
  "rewrite_query": "差旅 报销 标准 高铁 票据 要求"
}}

用户问题：{state["question"]}
当前查询词：{state.get("rewritten_question") or state["question"]}

知识库片段：
{format_docs_for_prompt(docs)}
"""
    result = llm.invoke([HumanMessage(content=prompt)])
    parsed = _parse_evaluation(result.content)
    rewritten_question = parsed["rewrite_query"] or state.get("rewritten_question") or state["question"]
    return {
        **state,
        "is_enough": parsed["is_enough"],
        "evaluation_reason": parsed["reason"],
        "rewritten_question": rewritten_question,
    }


def generate_node(state: AgentState) -> AgentState:
    docs = state.get("docs", [])
    if not docs:
        return {**state, "answer": "当前知识库中没有找到足够信息。\n\n引用来源：无"}

    llm = get_llm(temperature=0.2)
    user_prompt = f"""用户问题：
{state["question"]}

知识库片段：
{format_docs_for_prompt(docs)}

请严格基于以上知识库片段回答，并在答案最后列出引用来源。"""
    result = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
    )
    answer = result.content.strip()
    if "来源:" not in answer and "来源：" not in answer:
        citations = "\n".join(format_doc_source(doc) for doc in docs)
        answer = f"{answer}\n\n引用来源：\n{citations}"
    return {**state, "answer": answer}


def should_retry(state: AgentState) -> str:
    if state.get("is_enough"):
        return "generate"
    retry_count = state.get("retry_count", 0)
    if retry_count >= MAX_RETRY:
        return "generate"
    return "retry"


def increment_retry_node(state: AgentState) -> AgentState:
    return {**state, "retry_count": state.get("retry_count", 0) + 1}


def build_agent_graph(retriever: Any):
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", lambda state: retrieve_node(state, retriever))
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("increment_retry", increment_retry_node)
    graph.add_node("generate", generate_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        should_retry,
        {"generate": "generate", "retry": "increment_retry"},
    )
    graph.add_edge("increment_retry", "retrieve")
    graph.add_edge("generate", END)
    return graph.compile()


def ask_question(
    question: str,
    retriever: Any,
    selected_kbs: list[dict] | None = None,
    username: str = "",
    role: str = "",
) -> AgentState:
    selected_kbs = selected_kbs or []
    start = time.perf_counter()
    app = build_agent_graph(retriever)
    state: AgentState = app.invoke(
        {
            "question": question,
            "rewritten_question": question,
            "docs": [],
            "answer": "",
            "is_enough": False,
            "retry_count": 0,
            "evaluation_reason": "",
        }
    )
    latency = round(time.perf_counter() - start, 3)
    write_query_log(
        {
            "username": username,
            "role": role,
            "question": question,
            "selected_kbs": [
                {"kb_id": kb.get("id"), "kb_name": kb.get("name")}
                for kb in selected_kbs
            ],
            "rewritten_question": state.get("rewritten_question", ""),
            "retrieved_docs": [doc_to_log_item(doc) for doc in state.get("docs", [])],
            "answer": state.get("answer", ""),
            "latency": latency,
            "retry_count": state.get("retry_count", 0),
            "evaluation_reason": state.get("evaluation_reason", ""),
        }
    )
    state["latency"] = latency
    return state
