from pydantic import BaseModel


class UserItem(BaseModel):
    id: int
    username: str
    role: str
    created_at: str | None = None
    is_active: int | bool
    permissions: list[str] = []


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


class SetActiveRequest(BaseModel):
    is_active: bool


class ResetPasswordRequest(BaseModel):
    password: str


class UpdatePermissionsRequest(BaseModel):
    kb_ids: list[str]
