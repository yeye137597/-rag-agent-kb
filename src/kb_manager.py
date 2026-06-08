import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from config import KNOWLEDGE_BASE_ROOT


class KnowledgeBaseInUseError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_kb_id(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip().lower()).strip("_")
    if not slug:
        slug = f"kb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    candidate = slug
    while (KNOWLEDGE_BASE_ROOT / candidate).exists():
        candidate = f"{slug}_{uuid4().hex[:6]}"
    return candidate


def _read_metadata(metadata_path: Path) -> dict:
    if not metadata_path.exists():
        return {}
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_metadata(metadata_path: Path, metadata: dict) -> None:
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_knowledge_bases() -> list[dict]:
    KNOWLEDGE_BASE_ROOT.mkdir(parents=True, exist_ok=True)
    knowledge_bases = []
    for kb_path in sorted(KNOWLEDGE_BASE_ROOT.iterdir()):
        if not kb_path.is_dir():
            continue
        metadata_path = kb_path / "metadata.json"
        metadata = _read_metadata(metadata_path)
        kb_id = metadata.get("id", kb_path.name)
        name = metadata.get("name", kb_id)
        knowledge_bases.append(
            {
                "id": kb_id,
                "name": name,
                "path": kb_path,
                "metadata": metadata,
            }
        )
    return knowledge_bases


def create_knowledge_base(name: str) -> dict:
    display_name = name.strip()
    if not display_name:
        raise ValueError("知识库名称不能为空。")

    kb_id = _safe_kb_id(display_name)
    paths = get_kb_paths(kb_id)
    for path in (paths["root"], paths["chroma_db"], paths["uploads"], paths["processed"]):
        path.mkdir(parents=True, exist_ok=True)

    metadata = {
        "name": display_name,
        "id": kb_id,
        "created_at": _now(),
        "updated_at": _now(),
        "file_count": 0,
        "chunk_count": 0,
    }
    _write_metadata(paths["metadata"], metadata)
    return {"id": kb_id, "name": display_name, "path": paths["root"], "metadata": metadata}


def get_kb_paths(kb_id: str) -> dict[str, Path]:
    safe_id = Path(kb_id).name
    root = KNOWLEDGE_BASE_ROOT / safe_id
    return {
        "root": root,
        "chroma_db": root / "chroma_db",
        "uploads": root / "uploads",
        "processed": root / "processed",
        "metadata": root / "metadata.json",
    }


def _assert_kb_path_safe(path: Path) -> Path:
    root = KNOWLEDGE_BASE_ROOT.resolve()
    target = path.resolve()
    if target == root or root not in target.parents:
        raise ValueError("拒绝删除：目标路径不在 data/knowledge_bases 下。")
    return target


def delete_knowledge_base(kb_id: str) -> None:
    paths = get_kb_paths(kb_id)
    target = _assert_kb_path_safe(paths["root"])
    if not target.exists():
        return

    last_error: Exception | None = None
    for attempt in range(5):
        try:
            shutil.rmtree(target)
            return
        except PermissionError as exc:
            last_error = exc
            if getattr(exc, "winerror", None) == 32:
                time.sleep(0.5)
                continue
            raise
        except OSError as exc:
            last_error = exc
            if getattr(exc, "winerror", None) == 32:
                time.sleep(0.5)
                continue
            raise

    raise KnowledgeBaseInUseError(
        "删除失败：该知识库正在被当前程序占用。请停止 Streamlit 后手动删除该知识库目录，或重启应用后再删除。"
    ) from last_error


def update_kb_metadata(
    kb_id: str,
    file_count: int | None = None,
    chunk_count: int | None = None,
    embedding: dict | None = None,
) -> dict:
    paths = get_kb_paths(kb_id)
    metadata = _read_metadata(paths["metadata"])
    if not metadata:
        metadata = {
            "name": kb_id,
            "id": kb_id,
            "created_at": _now(),
            "file_count": 0,
            "chunk_count": 0,
        }
    if file_count is not None:
        metadata["file_count"] = file_count
    if chunk_count is not None:
        metadata["chunk_count"] = chunk_count
    if embedding is not None:
        metadata["embedding"] = embedding
    metadata["updated_at"] = _now()
    paths["metadata"].parent.mkdir(parents=True, exist_ok=True)
    _write_metadata(paths["metadata"], metadata)
    return metadata
