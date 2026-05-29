from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".md", ".txt"}


def load_document(file_path: Path) -> list[Document]:
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"不支持的文件类型: {suffix}")

    if suffix == ".pdf":
        loader = PyPDFLoader(str(file_path))
    elif suffix == ".docx":
        loader = Docx2txtLoader(str(file_path))
    else:
        loader = TextLoader(str(file_path), encoding="utf-8", autodetect_encoding=True)

    docs = loader.load()
    for index, doc in enumerate(docs):
        doc.metadata = doc.metadata or {}
        doc.metadata["source"] = file_path.name
        doc.metadata["file_path"] = str(file_path)
        if "page" not in doc.metadata:
            doc.metadata["page"] = index + 1 if suffix == ".pdf" else None
    return docs


def load_documents(file_paths: list[Path]) -> tuple[list[Document], list[str]]:
    docs: list[Document] = []
    errors: list[str] = []
    for file_path in file_paths:
        try:
            docs.extend(load_document(file_path))
        except Exception as exc:
            errors.append(f"{file_path.name}: {exc}")
    return docs, errors

