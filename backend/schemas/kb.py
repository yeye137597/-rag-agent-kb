from pydantic import BaseModel


class KbResponse(BaseModel):
    id: str
    name: str
    file_count: int = 0
    chunk_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class CreateKbRequest(BaseModel):
    name: str


class UploadResponse(BaseModel):
    kb_id: str
    uploaded_files: list[str]


class FileItem(BaseModel):
    filename: str
    size: int
    suffix: str


class CleanRequest(BaseModel):
    filenames: list[str] | None = None


class CleanPreviewItem(BaseModel):
    filename: str
    original_chars: int = 0
    cleaned_chars: int = 0
    original_preview: str = ""
    cleaned_preview: str = ""
    cleaned_filename: str | None = None
    error: str = ""


class CleanResponse(BaseModel):
    kb_id: str
    cleaned_count: int
    items: list[CleanPreviewItem]


class BuildRequest(BaseModel):
    use_cleaned: bool = False
    filenames: list[str] | None = None


class BuildResponse(BaseModel):
    kb_id: str
    file_count: int
    chunk_count: int
    errors: list[str] = []
