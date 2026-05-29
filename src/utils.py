import re
from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document

from config import CHROMA_DIR, LOG_DIR, LOG_FILE, PROCESSED_DIR, UPLOAD_DIR


def ensure_directories() -> None:
    for path in (UPLOAD_DIR, PROCESSED_DIR, CHROMA_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)
    LOG_FILE.touch(exist_ok=True)


def safe_filename(filename: str) -> str:
    return Path(filename).name.replace("\\", "_").replace("/", "_")


def save_uploaded_file(uploaded_file, upload_dir: Path = UPLOAD_DIR) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / safe_filename(uploaded_file.name)
    with target_path.open("wb") as f:
        f.write(uploaded_file.getbuffer())
    return target_path


def clean_text(text: str) -> str:
    """Clean noisy exported-chat/document text while preserving body content."""
    cleaned_lines = []
    previous_blank = False

    separator_pattern = re.compile(r"^[=\-_*]{4,}$")
    message_pattern = re.compile(r"^#{0,2}\s*消息\s*\d+\s*$")
    file_size_pattern = re.compile(
        r"^[^\s]+\.(?:txt|pdf|md|docx|doc)\s+\d+(?:\.\d+)?\s*(?:KB|MB|GB|B)\s*$",
        re.IGNORECASE,
    )

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if separator_pattern.fullmatch(line):
            continue
        if message_pattern.fullmatch(line):
            continue
        if file_size_pattern.fullmatch(line):
            continue

        if not line:
            if cleaned_lines and not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue

        cleaned_lines.append(line)
        previous_blank = False

    return "\n".join(cleaned_lines).strip()


def cleaned_file_path(original_path: Path, processed_dir: Path = PROCESSED_DIR) -> Path:
    return processed_dir / f"{original_path.stem}_cleaned.txt"


def save_cleaned_text(original_path: Path, text: str, processed_dir: Path = PROCESSED_DIR) -> Path:
    processed_dir.mkdir(parents=True, exist_ok=True)
    target_path = cleaned_file_path(original_path, processed_dir)
    target_path.write_text(text, encoding="utf-8")
    return target_path


def format_doc_source(doc: Document) -> str:
    metadata = doc.metadata or {}
    kb_name = metadata.get("kb_name", "默认知识库")
    source = metadata.get("source", "unknown")
    page = metadata.get("page", "N/A")
    if page is None:
        page = "N/A"
    chunk_id = metadata.get("chunk_id", "N/A")
    return f"[知识库: {kb_name}, 来源: {source}, 页码: {page}, 片段ID: {chunk_id}]"


def format_docs_for_prompt(docs: Iterable[Document]) -> str:
    blocks = []
    for i, doc in enumerate(docs, start=1):
        blocks.append(
            f"片段 {i} {format_doc_source(doc)}\n"
            f"{doc.page_content.strip()}"
        )
    return "\n\n".join(blocks)


def doc_to_log_item(doc: Document) -> dict:
    metadata = doc.metadata or {}
    return {
        "kb_id": metadata.get("kb_id", ""),
        "kb_name": metadata.get("kb_name", ""),
        "source": metadata.get("source", ""),
        "page": metadata.get("page"),
        "chunk_id": metadata.get("chunk_id"),
        "content_preview": doc.page_content[:200].replace("\n", " "),
    }


def deduplicate_docs(docs: Iterable[Document]) -> list[Document]:
    seen = set()
    result = []
    for doc in docs:
        metadata = doc.metadata or {}
        key = (
            metadata.get("kb_id"),
            metadata.get("file_path"),
            metadata.get("page"),
            metadata.get("chunk_id"),
            doc.page_content[:80],
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(doc)
    return result

