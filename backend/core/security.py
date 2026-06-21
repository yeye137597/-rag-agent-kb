from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import os
import warnings

from fastapi import HTTPException, status


DEFAULT_JWT_SECRET_KEY = "dev-secret-change-me"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def get_jwt_secret_key() -> str:
    secret_key = os.getenv("JWT_SECRET_KEY", DEFAULT_JWT_SECRET_KEY)
    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env == "production" and secret_key == DEFAULT_JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY must be configured with a strong value in production")
    if secret_key == DEFAULT_JWT_SECRET_KEY:
        warnings.warn(
            "Using default JWT_SECRET_KEY. This is only acceptable for local development.",
            RuntimeWarning,
            stacklevel=2,
        )
    return secret_key


JWT_SECRET_KEY = get_jwt_secret_key()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _sign(message: str) -> str:
    digest = hmac.new(JWT_SECRET_KEY.encode("utf-8"), message.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def create_access_token(user: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user["user_id"]),
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "exp": int(expire.timestamp()),
    }
    header_part = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    message = f"{header_part}.{payload_part}"
    return f"{message}.{_sign(message)}"


def decode_access_token(token: str) -> dict:
    try:
        header_part, payload_part, signature = token.split(".")
        message = f"{header_part}.{payload_part}"
        expected_signature = _sign(message)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("bad signature")
        header = json.loads(_b64url_decode(header_part))
        if header.get("alg") != "HS256":
            raise ValueError("unsupported algorithm")
        payload = json.loads(_b64url_decode(payload_part))
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("expired")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    return {
        "user_id": int(payload["user_id"]),
        "username": payload["username"],
        "role": payload["role"],
    }


