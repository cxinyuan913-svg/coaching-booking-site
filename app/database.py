"""資料庫連線設定：SQLite engine 與 session（跟 coaching-record-tool 同一套寫法）。"""
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# 可用環境變數覆寫，測試時指向獨立的暫存資料庫，不會動到真實的 booking.db
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./booking.db")

# SQLite 須加 check_same_thread=False 才能在 FastAPI 多執行緒下使用
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依賴注入用：取得一個 session，用完自動關閉。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _add_column_if_missing(conn, table: str, column: str, ddl: str) -> None:
    existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
    if column not in existing:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))


def ensure_schema_migrations() -> None:
    """資料庫升級（跟 coaching-record-tool 同一套寫法）：create_all 只會建立
    還不存在的表，不會幫已存在的表補新欄位，雲端那份 booking.db 是舊版建的，
    所以新增欄位時要在這裡用 PRAGMA 檢查後手動 ALTER TABLE 補上。全新建立的
    資料庫（例如測試用的暫存 DB）create_all 已經建好完整欄位，檢查到存在就跳過。

    新增欄位的寫法：
        _add_column_if_missing(conn, "booking_requests", "amount", "FLOAT")
    NOT NULL 欄位一定要給 DEFAULT，不然既有資料列會加不上去。
    """
    with engine.begin() as conn:
        # 目前還沒有需要補的欄位，預約流程 v2（spec/booking_flow.md）會從這裡開始加
        pass
