"""公開課程介紹 API（GET /api/courses）的測試。"""
from conftest import create_session_type, create_venue, login_as_coach, register_student


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


def test_教練可以編輯課程說明與參考價(client):
    login_as_coach(client)
    course = create_session_type(client, name="60分鐘單堂", reference_price=0)

    res = client.patch(
        f"/api/admin/session_types/{course['id']}",
        json={"reference_price": 1500, "description": "一對一指導", "target_audience": "初學者"},
    )
    assert res.status_code == 200, res.text
    updated = res.json()
    assert updated["reference_price"] == 1500
    assert updated["description"] == "一對一指導"
    assert updated["target_audience"] == "初學者"
    # 沒送的欄位維持原值
    assert updated["name"] == "60分鐘單堂"
    assert updated["duration_minutes"] == 60


def test_說明可以清空但必填欄位送null不會被清掉(client):
    login_as_coach(client)
    course = create_session_type(client)
    client.patch(f"/api/admin/session_types/{course['id']}", json={"description": "暫時的說明"})

    res = client.patch(
        f"/api/admin/session_types/{course['id']}", json={"description": None, "name": None}
    )
    assert res.status_code == 200, res.text
    assert res.json()["description"] is None
    assert res.json()["name"] == course["name"]


def test_編輯不存在的課程回404(client):
    login_as_coach(client)
    res = client.patch("/api/admin/session_types/9999", json={"name": "x"})
    assert res.status_code == 404


def test_學生不能編輯課程(client):
    login_as_coach(client)
    course = create_session_type(client)
    client.post("/api/auth/logout")
    register_student(client)

    res = client.patch(f"/api/admin/session_types/{course['id']}", json={"reference_price": 1})
    assert res.status_code == 403


def test_已有開放時段的課程不能改時長(client):
    login_as_coach(client)
    venue = create_venue(client)
    course = create_session_type(client, duration_minutes=60)
    res = client.post(
        "/api/admin/slots",
        json={
            "venue_id": venue["id"],
            "session_type_id": course["id"],
            "dates": ["2099-01-01"],
            "start_time": "10:00",
        },
    )
    assert res.status_code == 201, res.text

    res = client.patch(f"/api/admin/session_types/{course['id']}", json={"duration_minutes": 90})
    assert res.status_code == 409
    # 時長不變的話其他欄位照常可以改
    res = client.patch(
        f"/api/admin/session_types/{course['id']}",
        json={"duration_minutes": 60, "reference_price": 1800},
    )
    assert res.status_code == 200, res.text
    assert res.json()["reference_price"] == 1800


def test_沒有時段在用的課程可以改時長(client):
    login_as_coach(client)
    course = create_session_type(client, duration_minutes=60)
    res = client.patch(f"/api/admin/session_types/{course['id']}", json={"duration_minutes": 90})
    assert res.status_code == 200, res.text
    assert res.json()["duration_minutes"] == 90
