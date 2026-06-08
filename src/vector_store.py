from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import CHROMA_DIR
from src.model_factory import get_embedding_model


def get_embeddings():
    return get_embedding_model()


def load_vector_store(chroma_dir: Path | str = CHROMA_DIR) -> Chroma:
    chroma_path = Path(chroma_dir)
    chroma_path.mkdir(parents=True, exist_ok=True)
    return Chroma(
        persist_directory=str(chroma_path),
        embedding_function=get_embeddings(),
    )


def build_vector_store(chunks: list[Document], chroma_dir: Path | str = CHROMA_DIR) -> Chroma:
    vector_store = load_vector_store(chroma_dir)
    if chunks:
        vector_store.add_documents(chunks)
    return vector_store
