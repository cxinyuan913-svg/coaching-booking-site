"""FastAPI 進入點。"""
import os
import secrets
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response

from app import models  # noqa: F401  匯入以註冊 ORM models 到 Base.metadata
from app.database import Base, SessionLocal, engine
from app.routers import admin, auth, bookings, slots
from app.seed import seed_coach_account

# 五張表一次建齊
Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    seed_coach_account(db)

app = FastAPI(title="教練預約網站")

_SECRET_FILE = Path(__file__).resolve().parent.parent / "session_secret.txt"


def _load_or_create_session_secret() -> str:
    """比照 coaching-record-tool 的 booking_api_token.txt 做法：優先讀環境
    變數 SESSION_SECRET_KEY，沒設定就在本機檔案自動產生一組並記住，不用
    每次部署都手動想一組密鑰。"""
    env_value = os.environ.get("SESSION_SECRET_KEY")
    if env_value:
        return env_value
    if _SECRET_FILE.exists():
        content = _SECRET_FILE.read_text(encoding="utf-8").strip()
        if content:
            return content
    secret = secrets.token_urlsafe(32)
    _SECRET_FILE.write_text(secret, encoding="utf-8")
    return secret


app.add_middleware(SessionMiddleware, secret_key=_load_or_create_session_secret())

app.include_router(auth.router)
app.include_router(slots.router)
app.include_router(bookings.router)
app.include_router(admin.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


class NoCacheStaticFiles(StaticFiles):
    """開發階段沒有建置流程、檔名也不會加版本號，瀏覽器預設的試探性快取會讓
    F5 重新整理讀到舊檔案，只能用 Cache-Control: no-cache 強制每次都跟伺服器
    重新驗證 ETag。"""

    def file_response(self, *args, **kwargs) -> Response:
        response = super().file_response(*args, **kwargs)
        response.headers["cache-control"] = "no-cache"
        return response


# 靜態頁面掛載於根路徑，須放在所有 /api 路由之後才不會攔截 API 請求
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")
app.mount("/", NoCacheStaticFiles(directory="static", html=True), name="pages")
