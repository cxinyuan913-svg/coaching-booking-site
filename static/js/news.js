// 最新消息頁：一次抓全部已發布的消息，分類篩選在前端做（消息量不大，不用每次切換都打 API）。
let allNews = [];

function renderNewsList(category) {
  const list = document.getElementById("news-list");
  const items = category === "all" ? allNews : allNews.filter((n) => n.category === category);
  list.innerHTML = items.length
    ? items.map(renderNewsCard).join("")
    : '<p style="color: var(--ink-3)">這個分類目前還沒有消息。</p>';
}

async function loadNews() {
  const list = document.getElementById("news-list");
  try {
    allNews = await api.get("/api/news");
  } catch (err) {
    list.innerHTML = '<p class="error-text">消息載入失敗，請稍後再試。</p>';
    return;
  }
  if (allNews.length === 0) {
    list.innerHTML = '<p style="color: var(--ink-3)">目前還沒有消息，近期活動請直接洽詢教練。</p>';
    return;
  }
  renderNewsList("all");
}

document.getElementById("news-filter").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-category]");
  if (!btn) return;
  document.querySelectorAll("#news-filter button").forEach((b) => b.classList.toggle("active", b === btn));
  renderNewsList(btn.dataset.category);
});

document.addEventListener("DOMContentLoaded", loadNews);
