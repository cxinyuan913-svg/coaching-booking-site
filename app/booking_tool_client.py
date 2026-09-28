"""呼叫 coaching-record-tool 的整合 API，教練核准預約申請時用來自動建立
正式課程，教練不用手動謄一次（見兩個專案之間的介接約定）。純 stdlib，
不為了這一個呼叫多裝一個 HTTP client 套件。
"""
import json
import os
import urllib.error
import urllib.request
from datetime import date, time


class BookingToolError(Exception):
    """呼叫失敗（連不上、場地名稱對不起來、時段衝突等）時拋出，訊息會存進
    BookingRequest.sync_error，讓教練在後台看得到「這筆為什麼卡住」，
    不用去翻 server log。"""


def _base_url() -> str:
    url = os.environ.get("COACHING_TOOL_BASE_URL")
    if not url:
        raise BookingToolError("尚未設定 COACHING_TOOL_BASE_URL 環境變數")
    return url.rstrip("/")


def _token() -> str:
    token = os.environ.get("COACHING_TOOL_API_TOKEN")
    if not token:
        raise BookingToolError("尚未設定 COACHING_TOOL_API_TOKEN 環境變數")
    return token


def create_lesson(
    *,
    venue_name: str,
    student_name: str,
    student_contact: str | None,
    lesson_date: date,
    start_time: time,
    duration_minutes: int,
    note: str | None = None,
) -> dict:
    """打教練工具的 POST /api/integrations/lessons。成功回傳教練工具給的
    課程資訊（見該端點的回應格式）；失敗一律拋 BookingToolError。"""
    payload = {
        "venue_name": venue_name,
        "student_name": student_name,
        "student_contact": student_contact,
        "date": lesson_date.isoformat(),
        "start_time": start_time.isoformat(),
        "duration": duration_minutes,
        "note": note,
    }
    request = urllib.request.Request(
        f"{_base_url()}/api/integrations/lessons",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_token()}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise BookingToolError(f"教練工具回應 {exc.code}：{detail}") from exc
    except urllib.error.URLError as exc:
        raise BookingToolError(f"連不上教練工具：{exc.reason}") from exc
