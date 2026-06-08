from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class RegisterResponse(BaseModel):
    ok: bool
    message: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    user_id: int


class UserResponse(BaseModel):
    username: str
    role: str
    user_id: int
