from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}


class AuthTokenResponse(BaseModel):
    token: str
    access_token: str
    token_type: str = "bearer"
    user_id: int
    user: UserResponse
