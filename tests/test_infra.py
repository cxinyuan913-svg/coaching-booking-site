"""基礎設施：台灣時間、資料庫升級。"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text

from app.database import _add_column_if_missing
from app.timeutil import now_taipei, today_taipei


def test_台灣時間固定是UTC加8不受伺服器時區影響():
    expected = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=8)
    assert abs((now_taipei() - expected).total_seconds()) < 5
    assert today_taipei() == now_taipei().date()


def test_資料庫升級會補上缺少的欄位且重複執行不會出錯(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE things (id INTEGER PRIMARY KEY)"))
        conn.execute(text("INSERT INTO things (id) VALUES (1)"))

    for _ in range(2):
        with engine.begin() as conn:
            _add_column_if_missing(conn, "things", "flag", "BOOLEAN NOT NULL DEFAULT 0")

    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, flag FROM things")).all()
    assert rows == [(1, 0)]
