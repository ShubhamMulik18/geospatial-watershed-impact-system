import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, description="User's login username")
    password: str = Field(..., min_length=1, max_length=256, description="User's plain password")

    model_config = ConfigDict(str_strip_whitespace=True)


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"

