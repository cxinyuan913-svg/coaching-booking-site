"""初始資料建立：教練自己的帳號（唯一一組 is_coach=True 的帳號）。"""
import os

from sqlalchemy.orm import Session

from app import models
from app.auth import hash_password


def seed_coach_account(db: Session) -> None:
    """僅在還沒有任何教練帳號時，用環境變數 COACH_EMAIL／COACH_PASSWORD
    建立一組；沒設定這兩個環境變數就跳過（開發時可以先用其他方式手動建立）。"""
    if db.query(models.User).filter(models.User.is_coach.is_(True)).first() is not None:
        return
    email = os.environ.get("COACH_EMAIL")
    password = os.environ.get("COACH_PASSWORD")
    if not email or not password:
        return
    db.add(
        models.User(
            email=email,
            password_hash=hash_password(password),
            name="教練",
            is_coach=True,
        )
    )
    db.commit()
