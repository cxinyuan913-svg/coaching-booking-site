# 雲端部署（badmintonlemon.com）

## 架構

跟 coaching-record-tool 放在**同一台 Vultr VPS**，但是獨立容器、獨立資料庫：

```
                         ┌─ badmintonlemon.com ───────→ coaching-booking-site:8000（本專案）
網際網路 → Caddy(80/443) ─┤
                         └─ admin.badmintonlemon.com ─→ coaching-record-tool:8000
```

- 主機的 80/443 由 coaching-record-tool 那套 compose 裡的 Caddy 佔用（同一台
  主機只能有一個 Caddy 負責 HTTPS），所以本專案的 compose **不開對外 port**，
  只接上兩邊共用的 Docker 網路 `badmintonlemon_web`，由 Caddy 依網域轉進來。
- 本專案呼叫教練工具的整合端點仍走公開網址
  `https://admin.badmintonlemon.com`，跟本機開發時一樣，不依賴容器網路。
- 資料庫在主機的 `~/coaching-booking-site/data/booking.db`，整個 `data/`
  資料夾掛進容器（不是單一檔案，原因見 `Dockerfile` 註解）。

| 項目 | 內容 |
|---|---|
| 網址 | https://badmintonlemon.com |
| 程式位置 | `/root/coaching-booking-site` |
| 容器 | `coaching-booking-site`（compose 檔 `docker-compose.cloud.yml`） |
| 資料庫 | `/root/coaching-booking-site/data/booking.db` |
| 機密設定 | `/root/coaching-booking-site/.env`（不進版控，欄位見 `.env.example`） |

---

## 第一次上線

以下指令都在 VPS 上執行（`ssh root@<VPS的IP>`）。

### 1. DNS（Cloudflare）

加一筆 `A`，名稱 `@`，內容是 VPS 的 IP，**Proxy 關閉（灰色雲朵）**——跟
`admin` 那筆一樣，讓 Caddy 自己跟 Let's Encrypt 拿憑證。

### 2. 建立兩邊共用的 Docker 網路（只要做一次）

```bash
docker network create badmintonlemon_web
```

### 3. 讓 VPS 能 clone 這個 repo

GitHub 的部署金鑰是「一個 repo 一把」，coaching-record-tool 那把不能共用，
要另外產生一把：

```bash
ssh-keygen -t ed25519 -f ~/.ssh/deploy_booking_site -N "" -C "vps-coaching-booking-site"
cat ~/.ssh/deploy_booking_site.pub
```

把印出來的公鑰貼到 GitHub：repo → Settings → Deploy keys → Add deploy key
（**不要**勾 Allow write access）。然後設定 SSH 用這把金鑰連這個 repo：

```bash
cat >> ~/.ssh/config <<'CFG'

Host github-booking-site
  HostName github.com
  User git
  IdentityFile ~/.ssh/deploy_booking_site
  IdentitiesOnly yes
CFG

cd ~ && git clone git@github-booking-site:cxinyuan913-svg/coaching-booking-site.git
```

### 4. 建立 `.env` 與資料夾

```bash
cd ~/coaching-booking-site
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # 產生 SESSION_SECRET_KEY
nano .env
```

要填的欄位：

- `COACH_EMAIL`／`COACH_PASSWORD`：雲端的教練帳號（第一次啟動時自動建立）
- `SESSION_SECRET_KEY`：上一行產生的值，**一定要填**
- `COACHING_TOOL_API_TOKEN`：跟教練工具的 `public_booking_api_token.txt` 同一組，
  可以直接從同台主機讀：`cat ~/coaching-record-tool/public_booking_api_token.txt`
- `DISCORD_WEBHOOK_URL`：選填

```bash
mkdir -p data && chown 1000:1000 data && chmod 600 .env
```

### 5. 啟動

```bash
docker compose -f docker-compose.cloud.yml up -d --build
docker compose -f docker-compose.cloud.yml ps        # STATUS 要是 healthy
docker compose -f docker-compose.cloud.yml logs --tail 30
```

### 6. 讓 Caddy 轉發 badmintonlemon.com

這一步改的是 **coaching-record-tool** 的 Caddyfile 與 compose（Caddy 加上
`badmintonlemon.com` 區塊、接上 `badmintonlemon_web` 網路），在那個 repo
改好、push 之後：

```bash
cd ~/coaching-record-tool && git pull && docker compose -f docker-compose.cloud.yml up -d
```

### 7. 驗證

```bash
curl -s https://badmintonlemon.com/api/health            # {"status":"ok"}
curl -s https://admin.badmintonlemon.com/api/health      # 教練工具也要照常
```

再用瀏覽器開 https://badmintonlemon.com ，用 `.env` 的教練帳號登入後台，
**實際新增一筆東西**（例如編輯課程）確認寫入正常——只測讀取看不出資料庫
權限問題。

### 8. 每日備份（cron）

```bash
mkdir -p /root/coaching-booking-site/backups   # cron 的 log 要寫在這裡，先建好
crontab -e
# 加這一行：台灣時間 03:10（UTC 19:10）備份，跟教練工具的 03:00 錯開
10 19 * * * sh /root/coaching-booking-site/scripts/backup_db.sh >> /root/coaching-booking-site/backups/cron.log 2>&1
```

---

## 之後更新網站

本機改好、測試通過、push 到 GitHub 之後，SSH 進主機：

```bash
cd ~/coaching-booking-site && git pull && docker compose -f docker-compose.cloud.yml up -d --build
```

更新後跟第一次上線一樣，**至少做一次寫入操作**確認正常。

改壞了要退回：`git log --oneline -5` 找到上一個 commit，`git checkout <commit>`
後再跑一次上面的 compose 指令。

## 常見問題

- **網站打不開、Caddy log 顯示連不到 coaching-booking-site**：兩邊容器沒有接
  在同一個網路上。`docker network inspect badmintonlemon_web` 看裡面有沒有
  `coaching-booking-site` 跟 Caddy 兩個容器。
- **登入後馬上又變成沒登入**：`.env` 沒填 `SESSION_SECRET_KEY`，或是用 http://
  連線（雲端開了 `SESSION_HTTPS_ONLY=1`，cookie 只走 HTTPS）。
- **讀取正常但送出預約／編輯課程回 500**：`data/` 資料夾權限不對，
  `chown -R 1000:1000 ~/coaching-booking-site/data` 後重啟容器。
