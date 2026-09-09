from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import AuthTokenOut, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


def user_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/register", response_model=AuthTokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    existing = db.query(User).filter(func.lower(User.email) == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    # Prototype bootstrap: the first account is the administrator. Later accounts
    # may choose Operator or Reviewer, but cannot self-promote to Admin.
    first_account = db.query(User.id).first() is None
    role = "admin" if first_account else payload.role
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token, expires_at = create_access_token(user)
    return AuthTokenOut(access_token=token, expires_at=expires_at, user=user_out(user))


@router.post("/login", response_model=AuthTokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is inactive")

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    token, expires_at = create_access_token(user)
    return AuthTokenOut(access_token=token, expires_at=expires_at, user=user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)
