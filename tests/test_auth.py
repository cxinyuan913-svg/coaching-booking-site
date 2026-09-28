"""帳號註冊／登入／權限的測試。"""
from conftest import login_as_coach, register_student


def test_註冊後自動登入且不能重複註冊同一個email(client):
    register_student(client, email="a@example.com")

    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["email"] == "a@example.com"
    assert res.json()["is_coach"] is False

    res = client.post(
        "/api/auth/register",
        json={"email": "a@example.com", "password": "another-password", "name": "重複"},
    )
    assert res.status_code == 400


def test_密碼太短會被擋下不能註冊(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "password": "1234567", "name": "測試"},
    )
    assert res.status_code == 422


def test_密碼錯誤或帳號不存在都無法登入(client):
    register_student(client, email="a@example.com", password="correct-password")
    client.post("/api/auth/logout")

    res = client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong-password"})
    assert res.status_code == 401

    res = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert res.status_code == 401


def test_未登入呼叫需要登入的端點會被拒絕(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401

    res = client.get("/api/bookings")
    assert res.status_code == 401


def test_一般學生帳號不能呼叫後台端點只有教練帳號可以(client):
    register_student(client)
    res = client.get("/api/admin/venues")
    assert res.status_code == 403

    client.post("/api/auth/logout")
    login_as_coach(client)
    res = client.get("/api/admin/venues")
    assert res.status_code == 200
