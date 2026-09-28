"""帳號註冊／登入／登出。"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_password, require_user, verify_password
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserRegister, request: Request, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first() is not None:
        raise HTTPException(status_code=400, detail="這個 email 已經註冊過了")
    user = models.User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        phone=payload.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    return user


@router.post("/login", response_model=schemas.UserOut)
def login(payload: schemas.LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    request.session["user_id"] = user.id
    return user


@router.post("/logout", status_code=204)
def logout(request: Request):
    request.session.clear()


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(require_user)):
    return user
