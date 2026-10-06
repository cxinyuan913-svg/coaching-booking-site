"""最新消息 API 的測試：公開 GET /api/news 與教練後台 /api/admin/news。"""
from datetime import date

from conftest import login_as_coach, register_student


def _post_news(client, **fields) -> dict:
    res = client.post("/api/admin/news", json={"title": "測試消息", **fields})
    assert res.status_code == 201, res.text
    return res.json()


def test_發布消息沒填日期預設今天(client):
    login_as_coach(client)
    news = _post_news(client, body="內文", category="class")
    assert news["published_on"] == date.today().isoformat()
    assert news["category"] == "class"
    assert news["is_published"] is True


def test_公開清單只看得到已發布且置頂優先再依日期新到舊(client):
    login_as_coach(client)
    _post_news(client, title="舊消息", published_on="2026-01-01")
    _post_news(client, title="新消息", published_on="2026-09-01")
    _post_news(client, title="置頂但比較舊", published_on="2025-12-01", is_pinned=True)
    _post_news(client, title="草稿", is_published=False)
    client.post("/api/auth/logout")

    res = client.get("/api/news")
    assert res.status_code == 200
    assert [n["title"] for n in res.json()] == ["置頂但比較舊", "新消息", "舊消息"]

    res = client.get("/api/news?limit=1")
    assert [n["title"] for n in res.json()] == ["置頂但比較舊"]


def test_後台看得到草稿(client):
    login_as_coach(client)
    _post_news(client, title="草稿", is_published=False)
    res = client.get("/api/admin/news")
    assert [n["title"] for n in res.json()] == ["草稿"]


def test_編輯消息只改有送的欄位且可以下架(client):
    login_as_coach(client)
    news = _post_news(client, title="原標題", body="原內文", link_url="https://example.com")

    res = client.patch(f"/api/admin/news/{news['id']}", json={"is_published": False, "link_url": None})
    assert res.status_code == 200, res.text
    updated = res.json()
    assert updated["is_published"] is False
    assert updated["link_url"] is None
    assert updated["title"] == "原標題"
    assert updated["body"] == "原內文"
    assert client.get("/api/news").json() == []


def test_刪除消息(client):
    login_as_coach(client)
    news = _post_news(client)
    assert client.delete(f"/api/admin/news/{news['id']}").status_code == 204
    assert client.delete(f"/api/admin/news/{news['id']}").status_code == 404
    assert client.patch(f"/api/admin/news/{news['id']}", json={"title": "x"}).status_code == 404


def test_連結只接受http開頭(client):
    login_as_coach(client)
    res = client.post("/api/admin/news", json={"title": "x", "link_url": "javascript:alert(1)"})
    assert res.status_code == 422
    news = _post_news(client, link_url="")
    assert news["link_url"] is None


def test_學生不能發布消息(client):
    register_student(client)
    res = client.post("/api/admin/news", json={"title": "x"})
    assert res.status_code == 403
