from pathlib import Path
from typing import Any

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

try:
    from langchain.retrievers import EnsembleRetriever
except Exception:
    from langchain_classic.retrievers import EnsembleRetriever

from config import CHROMA_DIR, TOP_K
from src.vector_store import load_vector_store


class MultiKnowledgeBaseRetriever:
    def __init__(self, knowledge_bases: list[dict], top_k: int = TOP_K):
        self.knowledge_bases = knowledge_bases
        self.top_k = top_k

    def invoke(self, query: str) -> list[Document]:
        docs: list[Document] = []
        for kb in self.knowledge_bases:
            retriever = build_chroma_retriever(
                chroma_dir=kb["paths"]["chroma_db"],
                top_k=self.top_k,
            )
            kb_docs = retriever.invoke(query)
            for doc in kb_docs:
                doc.metadata = doc.metadata or {}
                doc.metadata.setdefault("kb_id", kb["id"])
                doc.metadata.setdefault("kb_name", kb["name"])
            docs.extend(kb_docs)
        return docs[: self.top_k]

    def get_relevant_documents(self, query: str) -> list[Document]:
        return self.invoke(query)


def build_chroma_retriever(chroma_dir: Path | str = CHROMA_DIR, top_k: int = TOP_K):
    vector_store = load_vector_store(chroma_dir)
    return vector_store.as_retriever(search_kwargs={"k": top_k})


def build_bm25_retriever(docs: list[Document], top_k: int = TOP_K):
    bm25 = BM25Retriever.from_documents(docs)
    bm25.k = top_k
    return bm25


def build_hybrid_retriever(
    docs: list[Document],
    top_k: int = TOP_K,
    chroma_dir: Path | str = CHROMA_DIR,
):
    chroma_retriever = build_chroma_retriever(chroma_dir=chroma_dir, top_k=top_k)
    if not docs:
        return chroma_retriever

    try:
        bm25_retriever = build_bm25_retriever(docs, top_k)
    except Exception:
        return chroma_retriever

    return EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever],
        weights=[0.4, 0.6],
    )


def build_multi_kb_retriever(
    selected_kbs: list[dict[str, Any]],
    current_chunks_by_kb: dict[str, list[Document]] | None = None,
    top_k: int = TOP_K,
):
    if not selected_kbs:
        raise ValueError("请至少选择一个知识库。")

    current_chunks_by_kb = current_chunks_by_kb or {}
    if len(selected_kbs) == 1:
        kb = selected_kbs[0]
        chunks = current_chunks_by_kb.get(kb["id"], [])
        return build_hybrid_retriever(
            chunks,
            top_k=top_k,
            chroma_dir=kb["paths"]["chroma_db"],
        )

    return MultiKnowledgeBaseRetriever(selected_kbs, top_k=top_k)
