from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    password_confirmation: str = Field(min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    status: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class HealthResponse(BaseModel):
    status: str
    service: str

class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    size_bytes: int
    status: str
    uploaded_at: datetime