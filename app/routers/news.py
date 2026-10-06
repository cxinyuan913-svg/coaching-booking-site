"""公開的最新消息 API：首頁跑馬燈/輪播與 /news.html 用，不用登入就能查。
發布、編輯、下架在 admin.py（需要教練身分）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import repository, schemas
from app.database import get_db

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=list[schemas.NewsOut])
def list_news(limit: int | None = Query(default=None, ge=1, le=100), db: Session = Depends(get_db)):
    return repository.list_published_news(db, limit=limit)
