// 首頁最新消息預覽：抓 GET /api/news 前 3 則（置頂優先），全部消息在 /news.html。
async function loadNewsPreview() {
  const grid = document.getElementById("news-preview");
  if (!grid) return;
  try {
    const items = await api.get("/api/news?limit=3");
    if (items.length === 0) {
      grid.innerHTML = '<p style="color: var(--ink-3)">目前還沒有消息，近期活動請直接洽詢教練。</p>';
      return;
    }
    grid.innerHTML = items.map(renderNewsCard).join("");
  } catch (err) {
    grid.innerHTML = '<p class="error-text">消息載入失敗，請稍後再試。</p>';
  }
}

document.addEventListener("DOMContentLoaded", loadNewsPreview);
