# 教練預約網站：雲端部署用的容器（見 spec/cloud_deployment.md）
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY static/ static/

# 用非 root 使用者跑。資料庫放在 /app/data（整個資料夾掛載進來），不要只掛
# 單一 .db 檔：SQLite 寫入時要在同一資料夾建立 journal 檔，資料夾不可寫的話
# 讀取正常、寫入全部 500（coaching-record-tool 2026-09-29 上線當天踩過）。
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

ENV DATABASE_URL=sqlite:////app/data/booking.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
