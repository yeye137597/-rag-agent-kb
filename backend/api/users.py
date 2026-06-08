from fastapi import APIRouter, HTTPException, status

from backend.core.deps import CurrentUser
from backend.schemas.users import (
    CreateUserRequest,
    ResetPasswordRequest,
    SetActiveRequest,
    UpdatePermissionsRequest,
    UserItem,
)
from src.auth import (
    create_user,
    get_user_permissions,
    list_users,
    replace_user_read_permissions,
    reset_user_password,
    set_user_active,
    write_audit_log,
)


router = APIRouter()


def _require_admin(user: dict) -> None:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


def _get_user_or_404(user_id: int) -> dict:
    for user in list_users():
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


def _with_permissions(user: dict) -> UserItem:
    permissions = [
        item["kb_id"]
        for item in get_user_permissions(user["id"])
        if item.get("can_read")
    ]
    return UserItem(**user, permissions=permissions)


@router.get("", response_model=list[UserItem])
def get_users(current_user: CurrentUser) -> list[UserItem]:
    _require_admin(current_user)
    return [_with_permissions(user) for user in list_users()]


@router.post("", response_model=UserItem)
def add_user(payload: CreateUserRequest, current_user: CurrentUser) -> UserItem:
    _require_admin(current_user)
    try:
        create_user(payload.username, payload.password, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    write_audit_log(current_user["username"], "api_create_user", f"username={payload.username}, role={payload.role}")
    created = next(user for user in list_users() if user["username"] == payload.username.strip())
    return _with_permissions(created)


@router.put("/{user_id}/active", response_model=UserItem)
def update_active(user_id: int, payload: SetActiveRequest, current_user: CurrentUser) -> UserItem:
    _require_admin(current_user)
    target = _get_user_or_404(user_id)
    if target["id"] == current_user["user_id"] and not payload.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot disable current user")
    set_user_active(user_id, payload.is_active)
    write_audit_log(current_user["username"], "api_set_user_active", f"user_id={user_id}, active={payload.is_active}")
    return _with_permissions(_get_user_or_404(user_id))


@router.put("/{user_id}/password", response_model=UserItem)
def update_password(user_id: int, payload: ResetPasswordRequest, current_user: CurrentUser) -> UserItem:
    _require_admin(current_user)
    _get_user_or_404(user_id)
    try:
        reset_user_password(user_id, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    write_audit_log(current_user["username"], "api_reset_password", f"user_id={user_id}")
    return _with_permissions(_get_user_or_404(user_id))


@router.put("/{user_id}/permissions", response_model=UserItem)
def update_permissions(user_id: int, payload: UpdatePermissionsRequest, current_user: CurrentUser) -> UserItem:
    _require_admin(current_user)
    target = _get_user_or_404(user_id)
    if target["role"] == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin can access all knowledge bases")
    replace_user_read_permissions(user_id, payload.kb_ids)
    write_audit_log(current_user["username"], "api_update_user_permissions", f"user_id={user_id}, kb_ids={payload.kb_ids}")
    return _with_permissions(_get_user_or_404(user_id))
