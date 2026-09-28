"""密碼雜湊與登入狀態（session cookie）。

Session 用 Starlette 內建的 SessionMiddleware（FastAPI 本來就建在 Starlette
之上，不用另外裝套件），只在簽章 cookie 裡存 user_id，不是自己刻一套 token
系統——這個網站的使用情境（一個教練＋若干學生帳號）不需要更複雜的機制。
"""
import bcrypt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models
from app.database import get_db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User | None:
    """未登入回傳 None，讓瀏覽開放時段這種公開頁面也能用同一個依賴。"""
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.get(models.User, user_id)


def require_user(user: models.User | None = Depends(get_current_user)) -> models.User:
    """需要登入的動作（送出預約申請、查自己的申請）用這個，未登入回 401。"""
    if user is None:
        raise HTTPException(status_code=401, detail="請先登入")
    return user


def require_coach(user: models.User = Depends(require_user)) -> models.User:
    """後台頁面（管理時段／審核申請）用這個，不是教練帳號回 403。"""
    if not user.is_coach:
        raise HTTPException(status_code=403, detail="沒有權限")
    return user
