"""套件初始化：載入專案根目錄的 .env。

放在這裡是因為 app.database 等模組在 import 當下就會讀環境變數，
必須搶在任何 app.* 模組之前載入。純 stdlib 小解析器，不為此多裝
python-dotenv（跟 booking_tool_client 同樣的取捨）。
"""
import os
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _load_dotenv() -> None:
    """逐行讀 KEY=VALUE，忽略空行與 # 註解，值兩側的引號會去掉。
    用 setdefault：系統/啟動時設定的真實環境變數永遠優先於 .env。
    測試環境設 BOOKING_SITE_SKIP_DOTENV 跳過，避免測試讀到本機真實的
    整合設定（教練工具 token、Discord webhook）而對外發出請求。"""
    if os.environ.get("BOOKING_SITE_SKIP_DOTENV") or not _ENV_FILE.exists():
        return
    for raw_line in _ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_dotenv()
