"""核心業務規則：開放時段、送出申請、核准／拒絕的完整流程。

呼叫教練工具的 booking_tool_client.create_lesson 全部用 monkeypatch 假掉，
不會真的打教練工具的 API。
"""
from datetime import date, timedelta

from app import models
from app.booking_tool_client import BookingToolError
from app.database import SessionLocal

from conftest import create_session_type, create_venue, login_as_coach, register_student


def _open_one_slot(client) -> dict:
    login_as_coach(client)
    venue = create_venue(client)
    session_type = create_session_type(client)
    slots = client.post(
        "/api/admin/slots",
        json={
            "venue_id": venue["id"],
            "session_type_id": session_type["id"],
            "dates": [(date.today() + timedelta(days=7)).isoformat()],
            "start_time": "18:00:00",
        },
    ).json()
    client.post("/api/auth/logout")
    return slots[0]


def test_批次開放時段後公開清單看得到且未來已訂走的看不到(client):
    login_as_coach(client)
    venue = create_venue(client)
    session_type = create_session_type(client)

    dates = [(date.today() + timedelta(days=i)).isoformat() for i in (3, 10, 17)]
    res = client.post(
        "/api/admin/slots",
        json={
            "venue_id": venue["id"],
            "session_type_id": session_type["id"],
            "dates": dates,
            "start_time": "18:00:00",
        },
    )
    assert res.status_code == 201, res.text
    assert len(res.json()) == 3
    client.post("/api/auth/logout")

    public = client.get("/api/slots").json()
    assert len(public) == 3
    assert {s["date"] for s in public} == set(dates)


def test_送出申請後時段還沒被標記已訂只有核准後才算數(client):
    slot = _open_one_slot(client)
    register_student(client)

    res = client.post("/api/bookings", json={"slot_id": slot["id"], "student_note": "第一次上課"})
    assert res.status_code == 201, res.text
    assert res.json()["status"] == "pending"

    public = client.get("/api/slots").json()
    assert len(public) == 1  # 還沒核准，時段還是開放的


def test_已經被訂走的時段不能再送出申請(client):
    slot = _open_one_slot(client)
    register_student(client, email="a@example.com")
    client.post("/api/bookings", json={"slot_id": slot["id"]})
    client.post("/api/auth/logout")

    with SessionLocal() as db:
        db.query(models.AvailabilitySlot).filter(models.AvailabilitySlot.id == slot["id"]).update(
            {"is_booked": True}
        )
        db.commit()

    register_student(client, email="b@example.com")
    res = client.post("/api/bookings", json={"slot_id": slot["id"]})
    assert res.status_code == 400


def test_核准申請成功後時段標記已訂且呼叫教練工具建立課程(client, monkeypatch):
    slot = _open_one_slot(client)
    register_student(client)
    booking = client.post("/api/bookings", json={"slot_id": slot["id"]}).json()
    client.post("/api/auth/logout")

    calls = []

    def fake_create_lesson(**kwargs):
        calls.append(kwargs)
        return {"lesson_id": 999, "student_id": 1, "student_created": True, "revenue_amount": 800}

    monkeypatch.setattr("app.routers.admin.create_lesson", fake_create_lesson)

    login_as_coach(client)
    res = client.post(f"/api/admin/bookings/{booking['id']}/approve")
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "approved"
    assert len(calls) == 1
    assert calls[0]["venue_name"] == slot["venue_name"]

    public = client.get("/api/slots").json()
    assert public == []  # 已經被約走，公開清單看不到了


def test_核准時呼叫教練工具失敗會留在pending並記錄錯誤訊息(client, monkeypatch):
    slot = _open_one_slot(client)
    register_student(client)
    booking = client.post("/api/bookings", json={"slot_id": slot["id"]}).json()
    client.post("/api/auth/logout")

    def fake_create_lesson(**kwargs):
        raise BookingToolError("教練工具回應 409：這個時間教練已經有其他課程了")

    monkeypatch.setattr("app.routers.admin.create_lesson", fake_create_lesson)

    login_as_coach(client)
    res = client.post(f"/api/admin/bookings/{booking['id']}/approve")
    assert res.status_code == 502

    pending = client.get("/api/admin/bookings?status=pending").json()
    assert len(pending) == 1
    assert "409" in pending[0]["sync_error"]

    public = client.get("/api/slots").json()
    assert len(public) == 1  # 核准失敗，時段不能被誤標成已訂走


def test_拒絕申請後時段重新開放(client):
    slot = _open_one_slot(client)
    register_student(client)
    booking = client.post("/api/bookings", json={"slot_id": slot["id"]}).json()
    client.post("/api/auth/logout")

    login_as_coach(client)
    res = client.post(f"/api/admin/bookings/{booking['id']}/reject")
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"

    public = client.get("/api/slots").json()
    assert len(public) == 1  # 拒絕後時段沒有被標記已訂，還是開放的


def test_核准一筆申請後同時段其他還沒處理的申請自動變成拒絕(client, monkeypatch):
    slot = _open_one_slot(client)
    register_student(client, email="a@example.com")
    booking_a = client.post("/api/bookings", json={"slot_id": slot["id"]}).json()
    client.post("/api/auth/logout")

    register_student(client, email="b@example.com")
    booking_b = client.post("/api/bookings", json={"slot_id": slot["id"]}).json()
    client.post("/api/auth/logout")

    monkeypatch.setattr(
        "app.routers.admin.create_lesson",
        lambda **kwargs: {"lesson_id": 1, "student_id": 1, "student_created": True, "revenue_amount": 800},
    )

    login_as_coach(client)
    client.post(f"/api/admin/bookings/{booking_a['id']}/approve")

    all_bookings = client.get("/api/admin/bookings").json()
    by_id = {b["id"]: b for b in all_bookings}
    assert by_id[booking_a["id"]]["status"] == "approved"
    assert by_id[booking_b["id"]]["status"] == "rejected"


def test_刪除已經被訂走的時段會被擋下(client):
    slot = _open_one_slot(client)
    with SessionLocal() as db:
        db.query(models.AvailabilitySlot).filter(models.AvailabilitySlot.id == slot["id"]).update(
            {"is_booked": True}
        )
        db.commit()

    login_as_coach(client)
    res = client.delete(f"/api/admin/slots/{slot['id']}")
    assert res.status_code == 400
