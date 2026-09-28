# 專案：教練預約網站（coaching-booking-site）

## 跟 coaching-record-tool 的關係

這是完全獨立的專案（獨立 repo、獨立資料庫、獨立部署），刻意跟
`coaching-record-tool`（教練自己用的記帳排課工具）分開，不共用資料庫、
不共用帳號系統——因為這個網站要對外開放任何人註冊，攻擊面不該直接接
在裝著教練真實收入/學生資料的那個資料庫上。詳見
`coaching-record-tool/spec/multi_user_architecture.md` 跟這個專案規劃
時的討論。

兩邊唯一的接點：教練在這個網站核准一筆預約申請後，會呼叫
`coaching-record-tool` 的 `POST /api/integrations/lessons`（Bearer
Token 驗證，見該專案的 `app/auth.py`／`app/routers/integrations.py`）
自動建立一堂正式課程，教練不用手動謄一次。

## 語言

以繁體中文溝通。程式碼註解使用繁體中文。

## 技術棧

- 後端：FastAPI + SQLAlchemy + SQLite
- 前端：原生 HTML / CSS / JavaScript（不用框架，跟 coaching-record-tool
  同樣的風格）
- 帳號：bcrypt 雜湊密碼 + Starlette SessionMiddleware（簽章 cookie），
  不是自己刻 token 系統
- 虛擬環境已建立於 `venv/`，套件清單見 `requirements.txt`

## 資料模型

五張表：`users`（帳號，`is_coach` 分教練/學生）、`venues`、
`session_types`、`availability_slots`（開放時段）、`booking_requests`
（預約申請，pending/approved/rejected）。跟 coaching-record-tool 一樣
一次建齊，不分批建立。

## 環境變數

- `COACH_EMAIL`／`COACH_PASSWORD`：第一次啟動時自動建立的教練帳號
- `SESSION_SECRET_KEY`：沒設定會自動產生並存到本機 `session_secret.txt`
- `COACHING_TOOL_BASE_URL`／`COACHING_TOOL_API_TOKEN`：呼叫
  coaching-record-tool 整合端點用，token 對應該專案的
  `public_booking_api_token.txt`

## 開發慣例

- 每完成一個小功能就 commit 一次，commit 訊息用繁體中文描述做了什麼
- 實作前先說明作法，等確認後再開始寫
- 一律避免用原生 `alert()`/`confirm()`——會整個鎖住分頁、無法用工具或
  程式化方式關掉；確認用 `common.js` 的 `confirmDialog()`，訊息用畫面
  上的文字區塊顯示，不要跳原生對話框
