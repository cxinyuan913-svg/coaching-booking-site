// 教練後台：發布／編輯／下架／刪除最新消息。同一張表單兼做新增與編輯，
// 按清單裡的「編輯」會把資料帶進表單、送出改成 PATCH。
let newsItems = [];

const form = document.getElementById("news-form");
const errorEl = document.getElementById("news-error");

function resetForm() {
  form.reset();
  document.getElementById("news-id").value = "";
  document.getElementById("news-date").value = toLocalDateString(new Date());
  document.getElementById("news-published").checked = true;
  document.getElementById("news-form-title").textContent = "發布新消息";
  document.getElementById("news-submit").textContent = "發布";
  document.getElementById("news-cancel").style.display = "none";
  errorEl.style.display = "none";
}

function statusText(n) {
  const parts = [n.is_published ? "已發布" : "草稿／下架"];
  if (n.is_pinned) parts.push("置頂");
  return parts.join("・");
}

async function loadNews() {
  newsItems = await api.get("/api/admin/news");
  const tbody = document.getElementById("news-admin-list");
  if (newsItems.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">還沒有消息</td></tr>';
    return;
  }
  tbody.innerHTML = newsItems
    .map(
      (n) => `<tr>
        <td>${n.published_on}</td>
        <td>${NEWS_CATEGORY_LABELS[n.category] || n.category}</td>
        <td>${escapeHtml(n.title)}</td>
        <td>${statusText(n)}</td>
        <td style="white-space: nowrap">
          <button type="button" class="secondary" data-action="edit" data-id="${n.id}">編輯</button>
          <button type="button" class="secondary" data-action="toggle" data-id="${n.id}">${n.is_published ? "下架" : "發布"}</button>
          <button type="button" class="danger" data-action="delete" data-id="${n.id}">刪除</button>
        </td>
      </tr>`
    )
    .join("");
}

function startEdit(n) {
  document.getElementById("news-id").value = n.id;
  document.getElementById("news-title").value = n.title;
  document.getElementById("news-category").value = n.category;
  document.getElementById("news-date").value = n.published_on;
  document.getElementById("news-body").value = n.body || "";
  document.getElementById("news-link").value = n.link_url || "";
  document.getElementById("news-published").checked = n.is_published;
  document.getElementById("news-pinned").checked = n.is_pinned;
  document.getElementById("news-form-title").textContent = "編輯消息";
  document.getElementById("news-submit").textContent = "儲存";
  document.getElementById("news-cancel").style.display = "";
  errorEl.style.display = "none";
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorEl.style.display = "none";
  const id = document.getElementById("news-id").value;
  const payload = {
    title: document.getElementById("news-title").value.trim(),
    category: document.getElementById("news-category").value,
    published_on: document.getElementById("news-date").value || null,
    body: document.getElementById("news-body").value.trim() || null,
    link_url: document.getElementById("news-link").value.trim() || null,
    is_published: document.getElementById("news-published").checked,
    is_pinned: document.getElementById("news-pinned").checked,
  };
  try {
    if (id) {
      await api.patch(`/api/admin/news/${id}`, payload);
    } else {
      await api.post("/api/admin/news", payload);
    }
  } catch (err) {
    errorEl.textContent = `儲存失敗：${err.message}`;
    errorEl.style.display = "";
    return;
  }
  resetForm();
  await loadNews();
});

document.getElementById("news-cancel").addEventListener("click", resetForm);

document.getElementById("news-admin-list").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const n = newsItems.find((item) => item.id === parseInt(btn.dataset.id, 10));
  if (!n) return;

  if (btn.dataset.action === "edit") {
    startEdit(n);
    return;
  }
  if (btn.dataset.action === "toggle") {
    await api.patch(`/api/admin/news/${n.id}`, { is_published: !n.is_published });
  } else if (btn.dataset.action === "delete") {
    if (!(await confirmDialog(`確定要刪除「${escapeHtml(n.title)}」嗎？刪除後無法復原，只想暫時隱藏請用「下架」。`))) return;
    await api.delete(`/api/admin/news/${n.id}`);
    if (document.getElementById("news-id").value === String(n.id)) resetForm();
  }
  await loadNews();
});

document.addEventListener("DOMContentLoaded", async () => {
  const user = await getCurrentUser();
  if (!user || !user.is_coach) {
    window.location.href = "/login.html";
    return;
  }
  resetForm();
  await loadNews();
});
