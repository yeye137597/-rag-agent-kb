import os

from fastapi import APIRouter, HTTPException, status

from backend.core.deps import CurrentUser
from backend.core.security import create_access_token
from backend.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, UserResponse
from src.auth import authenticate_user, register_user, write_audit_log


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        write_audit_log(payload.username.strip(), "api_login_failed", "invalid username or password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(user)
    write_audit_log(user["username"], "api_login_success", "login through FastAPI")
    return LoginResponse(token=token, **user)


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(**current_user)


@router.post("/register", response_model=RegisterResponse)
def register(payload: RegisterRequest) -> RegisterResponse:
    public_register_enabled = os.getenv("ENABLE_PUBLIC_REGISTER", "true").lower() == "true"
    if not public_register_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is disabled",
        )

    ok, message = register_user(payload.username, payload.password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return RegisterResponse(ok=True, message=message)

