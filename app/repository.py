"""資料存取封裝層。

目的：把「查資料庫」跟「路由/業務邏輯」分開一層，之後如果要把 SQLite
換成 Supabase，換掉的地方集中在這裡，不用去動每一支路由。

目前刻意只套用在新加的課程查詢上——現有 auth.py／admin.py／bookings.py／
slots.py 裡的查詢邏輯已經測過、穩定運作，全面套用這個模式是比較大的
改動，風險較高，之後真的要換 Supabase 再另外排一輪重構。
"""
from sqlalchemy.orm import Session

from app import models


def list_courses(db: Session) -> list[models.SessionType]:
    """首頁課程介紹卡片用：列出所有課程種類，依建立順序排序。"""
    return db.query(models.SessionType).order_by(models.SessionType.id).all()
