#!/bin/sh
# 每天備份 data/booking.db，保留最近 14 天，用 cron 排程執行（見
# spec/cloud_deployment.md）。用 sqlite3 的 .backup 而不是直接 cp，避免
# 剛好有人在送預約申請、寫到一半時複製到不完整的檔案。
#
# 這是 VPS 本機端的備份，跟資料庫在同一顆硬碟上；要防主機整台掛掉，還是要
# 定期把 backups/ 抓回本機或上傳到別處。

set -eu

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$APP_DIR/backups"
RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR"
docker exec coaching-booking-site python -c "
import sqlite3
src = sqlite3.connect('/app/data/booking.db')
dst = sqlite3.connect('/app/data/backup_tmp.db')
src.backup(dst)
dst.close()
src.close()
"
mv "$APP_DIR/data/backup_tmp.db" "$BACKUP_DIR/booking_$(date +%Y%m%d_%H%M%S).db"

find "$BACKUP_DIR" -name 'booking_*.db' -mtime "+$RETENTION_DAYS" -delete
