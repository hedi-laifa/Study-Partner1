import hashlib

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, UserResponse
from app.services.user_seeder import seed_new_user_workspace

router = APIRouter(prefix="/auth", tags=["auth"])


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokenResponse(BaseModel):
    token: str
    access_token: str
    token_type: str = "bearer"
    user_id: int
    user: UserResponse


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=body.email, password_hash=_hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize rich dynamic starter courses and practice exams for this user
    try:
        seed_new_user_workspace(db, user)
    except Exception as exc:
        print("User seeder error:", exc)

    return user


@router.post("/login", response_model=AuthTokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or user.password_hash != _hash_password(body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Ensure this user has dynamic courses and practice exams
    try:
        seed_new_user_workspace(db, user)
    except Exception as exc:
        print("User seeder error on login:", exc)

    token = f"user_{user.id}"
    return AuthTokenResponse(
        token=token,
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    x_user_id: int | None = Header(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = x_user_id
    if not user_id and authorization and "user_" in authorization:
        try:
            user_id = int(authorization.split("user_")[-1].strip())
        except (ValueError, IndexError):
            pass
    if not user_id:
        user_id = 1
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
