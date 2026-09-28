"""公開課程介紹 API（GET /api/courses）的測試。"""
from conftest import create_session_type, login_as_coach


def test_不用登入就能查詢課程清單(client):
    login_as_coach(client)
    create_session_type(
        client,
        name="一對一私人課",
        duration_minutes=60,
        reference_price=1200,
    )
    client.post("/api/auth/logout")

    res = client.get("/api/courses")
    assert res.status_code == 200
    courses = res.json()
    assert len(courses) == 1
    assert courses[0]["name"] == "一對一私人課"


def test_課程說明與適合對象可以是空值(client):
    login_as_coach(client)
    res = client.post(
        "/api/admin/session_types",
        json={
            "name": "小班團體課",
            "duration_minutes": 90,
            "reference_price": 800,
            "description": "初階/中階/進階皆可，8堂一期",
            "target_audience": "想跟朋友一起練習的學員",
        },
    )
    assert res.status_code == 201, res.text
    client.post("/api/auth/logout")

    res = client.get("/api/courses")
    course = res.json()[0]
    assert course["description"] == "初階/中階/進階皆可，8堂一期"
    assert course["target_audience"] == "想跟朋友一起練習的學員"
