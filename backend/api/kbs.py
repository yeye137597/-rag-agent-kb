from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.core.deps import CurrentUser
from backend.schemas.kb import (
    BuildRequest,
    BuildResponse,
    CleanPreviewItem,
    CleanRequest,
    CleanResponse,
    CreateKbRequest,
    FileItem,
    KbResponse,
    UploadResponse,
)
from src.auth import get_authorized_kb_ids, write_audit_log
from src.document_loader import SUPPORTED_SUFFIXES, load_documents
from src.kb_manager import (
    KnowledgeBaseInUseError,
    create_knowledge_base,
    delete_knowledge_base,
    get_kb_paths,
    list_knowledge_bases,
    update_kb_metadata,
)
from src.splitter import split_documents
from src.utils import clean_text, safe_filename, save_cleaned_text
from src.vector_store import build_vector_store


router = APIRouter()


def _kb_to_response(kb: dict) -> KbResponse:
    metadata = kb.get("metadata") or {}
    return KbResponse(
        id=kb["id"],
        name=kb["name"],
        file_count=int(metadata.get("file_count", 0) or 0),
        chunk_count=int(metadata.get("chunk_count", 0) or 0),
        created_at=metadata.get("created_at"),
        updated_at=metadata.get("updated_at"),
    )


def _visible_kbs(user: dict) -> list[dict]:
    all_kbs = list_knowledge_bases()
    if user["role"] == "admin":
        return all_kbs
    allowed_ids = get_authorized_kb_ids(user["user_id"], write_required=False)
    return [kb for kb in all_kbs if kb["id"] in allowed_ids]


def _require_admin(user: dict) -> None:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


def _can_write_kb(user: dict, kb_id: str) -> bool:
    if user["role"] == "admin":
        return True
    return kb_id in get_authorized_kb_ids(user["user_id"], write_required=True)


def _require_kb_write(user: dict, kb_id: str) -> None:
    if not _can_write_kb(user, kb_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No write access to this knowledge base")


def _get_kb_or_404(kb_id: str) -> dict:
    for kb in list_knowledge_bases():
        if kb["id"] == kb_id:
            return kb
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")


def _add_kb_metadata(chunks: list, kb_id: str, kb_name: str) -> list:
    for chunk in chunks:
        chunk.metadata = chunk.metadata or {}
        chunk.metadata["kb_id"] = kb_id
        chunk.metadata["kb_name"] = kb_name
    return chunks


def _file_items(paths: list[Path]) -> list[FileItem]:
    return [
        FileItem(filename=path.name, size=path.stat().st_size, suffix=path.suffix.lower())
        for path in paths
        if path.exists() and path.is_file()
    ]


def _supported_files(directory: Path, filenames: list[str] | None = None) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    selected = {safe_filename(name) for name in filenames} if filenames else None
    result = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if selected is not None and path.name not in selected:
            continue
        result.append(path)
    return result


def _extract_plain_text(file_path: Path) -> str:
    documents, errors = load_documents([file_path])
    if errors:
        raise RuntimeError("; ".join(errors))
    return "\n\n".join(doc.page_content for doc in documents)


@router.get("", response_model=list[KbResponse])
def list_kbs(current_user: CurrentUser) -> list[KbResponse]:
    return [_kb_to_response(kb) for kb in _visible_kbs(current_user)]


@router.post("", response_model=KbResponse)
def create_kb(payload: CreateKbRequest, current_user: CurrentUser) -> KbResponse:
    _require_admin(current_user)
    try:
        kb = create_knowledge_base(payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    write_audit_log(current_user["username"], "api_create_kb", f"{kb['name']} ({kb['id']})")
    return _kb_to_response(kb)


@router.post("/{kb_id}/upload", response_model=UploadResponse)
async def upload_files(
    kb_id: str,
    current_user: CurrentUser,
    files: list[UploadFile] = File(...),
) -> UploadResponse:
    kb = _get_kb_or_404(kb_id)
    _require_kb_write(current_user, kb_id)
    paths = get_kb_paths(kb_id)
    paths["uploads"].mkdir(parents=True, exist_ok=True)

    saved_files = []
    for file in files:
        filename = safe_filename(file.filename or "")
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {suffix}",
            )
        target = paths["uploads"] / filename
        content = await file.read()
        target.write_bytes(content)
        saved_files.append(filename)

    write_audit_log(current_user["username"], "api_upload_files", f"kb_id={kb['id']}, files={len(saved_files)}")
    return UploadResponse(kb_id=kb_id, uploaded_files=saved_files)


@router.get("/{kb_id}/files", response_model=dict[str, list[FileItem]])
def list_files(kb_id: str, current_user: CurrentUser) -> dict[str, list[FileItem]]:
    _get_kb_or_404(kb_id)
    _require_kb_write(current_user, kb_id)
    paths = get_kb_paths(kb_id)
    uploads = _supported_files(paths["uploads"])
    processed = _supported_files(paths["processed"])
    return {"uploads": _file_items(uploads), "processed": _file_items(processed)}


@router.post("/{kb_id}/clean", response_model=CleanResponse)
def clean_files(
    kb_id: str,
    current_user: CurrentUser,
    payload: CleanRequest | None = None,
) -> CleanResponse:
    kb = _get_kb_or_404(kb_id)
    _require_kb_write(current_user, kb_id)
    paths = get_kb_paths(kb_id)
    upload_paths = _supported_files(paths["uploads"], payload.filenames if payload else None)
    if not upload_paths:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No supported files to clean")

    items: list[CleanPreviewItem] = []
    for file_path in upload_paths:
        try:
            original_text = _extract_plain_text(file_path)
            cleaned_text = clean_text(original_text)
            cleaned_path = save_cleaned_text(file_path, cleaned_text, paths["processed"])
            items.append(
                CleanPreviewItem(
                    filename=file_path.name,
                    original_chars=len(original_text),
                    cleaned_chars=len(cleaned_text),
                    original_preview=original_text[:500],
                    cleaned_preview=cleaned_text[:500],
                    cleaned_filename=cleaned_path.name,
                )
            )
        except Exception as exc:
            items.append(CleanPreviewItem(filename=file_path.name, error=str(exc)))

    cleaned_count = len([item for item in items if not item.error])
    write_audit_log(current_user["username"], "api_clean_files", f"kb_id={kb['id']}, cleaned={cleaned_count}")
    return CleanResponse(kb_id=kb_id, cleaned_count=cleaned_count, items=items)


@router.post("/{kb_id}/build", response_model=BuildResponse)
def build_kb(
    kb_id: str,
    current_user: CurrentUser,
    payload: BuildRequest | None = None,
) -> BuildResponse:
    kb = _get_kb_or_404(kb_id)
    _require_kb_write(current_user, kb_id)
    paths = get_kb_paths(kb_id)
    payload = payload or BuildRequest()
    source_dir = paths["processed"] if payload.use_cleaned else paths["uploads"]
    build_paths = _supported_files(source_dir, payload.filenames)
    if not build_paths:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No supported files uploaded")

    documents, errors = load_documents(build_paths)
    chunks = _add_kb_metadata(split_documents(documents), kb_id=kb["id"], kb_name=kb["name"])
    build_vector_store(chunks, paths["chroma_db"])
    metadata = update_kb_metadata(kb_id, file_count=len(build_paths), chunk_count=len(chunks))
    write_audit_log(current_user["username"], "api_build_kb", f"kb_id={kb_id}, chunks={len(chunks)}")
    return BuildResponse(
        kb_id=kb_id,
        file_count=int(metadata.get("file_count", len(build_paths))),
        chunk_count=int(metadata.get("chunk_count", len(chunks))),
        errors=errors,
    )


@router.delete("/{kb_id}")
def delete_kb(kb_id: str, current_user: CurrentUser) -> dict:
    _require_admin(current_user)
    _get_kb_or_404(kb_id)
    try:
        delete_knowledge_base(kb_id)
    except KnowledgeBaseInUseError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    write_audit_log(current_user["username"], "api_delete_kb", kb_id)
    return {"ok": True, "kb_id": kb_id}
