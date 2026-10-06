"""統一取得「台灣當地時間」（跟 coaching-record-tool 的 app/timeutil.py 同一套寫法）。

資料庫裡的日期時間存的是沒有時區的台灣當地時間，所以程式裡的「現在／今天」
也一定要是台灣時間。不能用 datetime.now()／date.today()：那是伺服器所在時區的
時間，本機 Windows 剛好設台灣時區所以沒事，但雲端 Docker 容器預設是 UTC，會慢
8 小時（「提前 7 天」「24 小時內付款」這類規則都會算錯）。
"""
from datetime import date, datetime, timedelta, timezone

TAIWAN_TZ = timezone(timedelta(hours=8))


def now_taipei() -> datetime:
    """台灣當地時間，不帶時區（跟資料庫的存法一致，可以直接比較）。"""
    return datetime.now(TAIWAN_TZ).replace(tzinfo=None)


def today_taipei() -> date:
    return now_taipei().date()
