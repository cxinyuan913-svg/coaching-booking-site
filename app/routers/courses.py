"""公開的課程介紹 API：首頁課程卡片用，不用登入就能查。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import repository, schemas
from app.database import get_db

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=list[schemas.SessionTypeOut])
def list_courses(db: Session = Depends(get_db)):
    return repository.list_courses(db)
