from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma_db"
KNOWLEDGE_BASE_ROOT = DATA_DIR / "knowledge_bases"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "query_logs.jsonl"
DB_FILE = DATA_DIR / "app.db"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 5
MAX_RETRY = 2

EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

load_dotenv(BASE_DIR / ".env")

for path in (UPLOAD_DIR, PROCESSED_DIR, CHROMA_DIR, KNOWLEDGE_BASE_ROOT, LOG_DIR):
    path.mkdir(parents=True, exist_ok=True)
