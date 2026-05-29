import json
from datetime import datetime

from config import LOG_FILE


def write_query_log(record: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {"time": datetime.now().isoformat(timespec="seconds"), **record}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

