import hashlib
import hmac
import os
import re
import sqlite3

from src.db import get_connection, init_db, now_text


try:
    from passlib.context import CryptContext
except ImportError:
    CryptContext = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext else None
USERNAME_PATTERN = re.compile(r"^[\u4e00-\u9fa5A-Za-z0-9_-]+$")


def hash_password(password: str) -> str:
    if pwd_context:
        try:
            return pwd_context.hash(password)
        except Exception:
            pass
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        if password_hash.startswith("pbkdf2_sha256$"):
            _, salt, digest = password_hash.split("$", 2)
            candidate = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                120000,
            ).hex()
            return hmac.compare_digest(candidate, digest)
        if pwd_context:
            return pwd_context.verify(password, password_hash)
        return False
    except Exception:
        return False


def validate_username(username: str) -> str | None:
    if not username.strip():
        return "Username cannot be empty"
    if not USERNAME_PATTERN.fullmatch(username.strip()):
        return "Username can only contain Chinese characters, letters, numbers, underscores, and hyphens"
    return None


def validate_password(password: str) -> str | None:
    if not password:
        return "Password cannot be empty"
    if len(password) < 6:
        return "Password must be at least 6 characters"
    return None


def initialize_auth() -> None:
    init_db()
    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env == "production" and admin_password == "admin123":
        raise RuntimeError("ADMIN_PASSWORD must be configured with a strong value in production")

    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        if count == 0:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (admin_username, hash_password(admin_password), "admin", now_text()),
            )
            conn.commit()

def authenticate_user(username: str, password: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, is_active FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
    if not row or not row["is_active"]:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return {
        "user_id": row["id"],
        "username": row["username"],
        "role": row["role"],
    }


def register_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()
    username_error = validate_username(username)
    if username_error:
        return False, username_error
    password_error = validate_password(password)
    if password_error:
        return False, password_error

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at, is_active)
                VALUES (?, ?, 'user', ?, 1)
                """,
                (username, hash_password(password), now_text()),
            )
            conn.commit()
        write_audit_log(username, "register_user", f"鐢ㄦ埛 {username} 鑷姪娉ㄥ唽")
        return True, "Registration successful. Please log in. New accounts have no knowledge base permissions by default; contact an administrator for access."
    except sqlite3.IntegrityError:
        write_audit_log(username, "娉ㄥ唽澶辫触锛岀敤鎴峰悕閲嶅", f"username={username}")
        return False, "Username already exists. Please choose another username."
    except Exception:
        return False, "Registration failed. Please try again later."


def create_user(username: str, password: str, role: str) -> None:
    username = username.strip()
    username_error = validate_username(username)
    if username_error:
        raise ValueError(username_error)
    password_error = validate_password(password)
    if password_error:
        raise ValueError(password_error)
    if role not in {"admin", "user"}:
        raise ValueError("Role must be admin or user.")
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (username, hash_password(password), role, now_text()),
            )
            conn.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError("Username already exists. Please choose another username.") from exc


def list_users() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at, is_active FROM users ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def set_user_active(user_id: int, is_active: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, user_id),
        )
        conn.commit()


def reset_user_password(user_id: int, new_password: str) -> None:
    password_error = validate_password(new_password)
    if password_error:
        raise ValueError(password_error)
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id),
        )
        conn.commit()


def upsert_kb_permission(user_id: int, kb_id: str, can_read: bool, can_write: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_kb_permissions (user_id, kb_id, can_read, can_write, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, kb_id)
            DO UPDATE SET can_read = excluded.can_read, can_write = excluded.can_write
            """,
            (user_id, kb_id, 1 if can_read else 0, 1 if can_write else 0, now_text()),
        )
        conn.commit()


def replace_user_read_permissions(user_id: int, kb_ids: list[str]) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM user_kb_permissions WHERE user_id = ?", (user_id,))
        for kb_id in kb_ids:
            conn.execute(
                """
                INSERT INTO user_kb_permissions (user_id, kb_id, can_read, can_write, created_at)
                VALUES (?, ?, 1, 0, ?)
                """,
                (user_id, kb_id, now_text()),
            )
        conn.commit()


def get_user_permissions(user_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT user_id, kb_id, can_read, can_write, created_at
            FROM user_kb_permissions
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_authorized_kb_ids(user_id: int, write_required: bool = False) -> set[str]:
    column = "can_write" if write_required else "can_read"
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT kb_id FROM user_kb_permissions WHERE user_id = ? AND {column} = 1",
            (user_id,),
        ).fetchall()
    return {row["kb_id"] for row in rows}


def write_audit_log(username: str, action: str, detail: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs (username, action, detail, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, action, detail, now_text()),
        )
        conn.commit()


def list_audit_logs(limit: int = 100) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT username, action, detail, created_at
            FROM audit_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]

