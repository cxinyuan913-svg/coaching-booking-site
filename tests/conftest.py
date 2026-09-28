"""測試共用設定。

最重要的規則：絕對不能碰到真實在用的 booking.db。這裡在匯入任何 app
模組之前，先把 DATABASE_URL 指向一個獨立的暫存檔案，之後每個測試執行
前都會把這個暫存資料庫整個重建一次，確保測試之間互不影響。
"""
import os
import tempfile

import pytest

_tmp_dir = tempfile.mkdtemp(prefix="booking_site_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp_dir, 'test_booking.db')}"
os.environ["SESSION_SECRET_KEY"] = "test-session-secret-key"
os.environ["COACH_EMAIL"] = "coach@example.com"
os.environ["COACH_PASSWORD"] = "coach-test-password"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_coach_account  # noqa: E402

COACH_EMAIL = os.environ["COACH_EMAIL"]
COACH_PASSWORD = os.environ["COACH_PASSWORD"]


@pytest.fixture()
def client():
    """每個測試都拿到一份乾淨的資料庫（只有種好的教練帳號），互相隔離。"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_coach_account(db)
    return TestClient(app)


def login_as_coach(client: TestClient) -> dict:
    res = client.post("/api/auth/login", json={"email": COACH_EMAIL, "password": COACH_PASSWORD})
    assert res.status_code == 200, res.text
    return res.json()


def register_student(
    client: TestClient, email: str = "student@example.com", password: str = "testpass123", name: str = "測試學生"
) -> dict:
    res = client.post("/api/auth/register", json={"email": email, "password": password, "name": name})
    assert res.status_code == 201, res.text
    return res.json()


def create_venue(client: TestClient, name: str = "測試場館") -> dict:
    res = client.post("/api/admin/venues", json={"name": name})
    assert res.status_code == 201, res.text
    return res.json()


def create_session_type(
    client: TestClient, name: str = "60分鐘", duration_minutes: int = 60, reference_price: float = 800
) -> dict:
    res = client.post(
        "/api/admin/session_types",
        json={"name": name, "duration_minutes": duration_minutes, "reference_price": reference_price},
    )
    assert res.status_code == 201, res.text
    return res.json()
