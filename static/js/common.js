// 共用 fetch 工具與導覽列 active 狀態標示（跟 coaching-record-tool 的
// static/js/common.js 同一套，直接搬過來用）

async function apiRequest(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch (e) {
      // 忽略非 JSON 錯誤內容
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

const api = {
  get: (url) => apiRequest("GET", url),
  post: (url, body) => apiRequest("POST", url, body),
  delete: (url) => apiRequest("DELETE", url),
};

// 置中的確認視窗，取代原生 confirm()
function confirmDialog(message) {
  return new Promise((resolve) => {
    const backdrop = document.createElement("div");
    backdrop.className = "modal-backdrop open";
    backdrop.innerHTML = `
      <div class="modal" style="max-width: 360px">
        <p style="margin-top: 0; white-space: pre-wrap">${message}</p>
        <div class="modal-actions">
          <button type="button" class="secondary" data-role="cancel">取消</button>
          <button type="button" class="danger" data-role="confirm">確定</button>
        </div>
      </div>
    `;
    document.body.appendChild(backdrop);

    function finish(result) {
      backdrop.remove();
      resolve(result);
    }

    backdrop.querySelector('[data-role="confirm"]').addEventListener("click", () => finish(true));
    backdrop.querySelector('[data-role="cancel"]').addEventListener("click", () => finish(false));
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) finish(false);
    });
  });
}

function highlightActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll("nav.topnav a").forEach((a) => {
    if (a.getAttribute("href") === path) {
      a.classList.add("active");
    }
  });
}

// 依登入狀態組出導覽列連結：未登入只看得到登入/註冊；一般學生看得到
// 開放時段／我的預約；教練看得到後台的兩個管理頁，並且都比一般連結多一個
// 登出。放在 common.js 統一處理，每個頁面的 <nav id="topnav"> 都空著讓
// 這裡填，不用每頁各自寫一份判斷邏輯。
async function renderNav() {
  const nav = document.getElementById("topnav");
  if (!nav) return;
  const user = await getCurrentUser();

  const links = [];
  if (user && user.is_coach) {
    links.push(["/", "首頁"]);
    links.push(["/admin_slots.html", "開放時段管理"]);
    links.push(["/admin_requests.html", "審核申請"]);
  } else {
    links.push(["/", "首頁"]);
    links.push(["/book.html", "立即預約"]);
    if (user) links.push(["/my_bookings.html", "我的預約"]);
  }

  nav.innerHTML = links.map(([href, label]) => `<a href="${href}">${label}</a>`).join("");

  if (user) {
    const logout = document.createElement("a");
    logout.href = "#";
    logout.textContent = "登出";
    logout.addEventListener("click", async (e) => {
      e.preventDefault();
      await api.post("/api/auth/logout", null).catch(() => {});
      window.location.href = "/login.html";
    });
    nav.appendChild(logout);
  } else {
    nav.innerHTML += '<a href="/login.html">登入</a><a href="/register.html">註冊</a>';
  }

  highlightActiveNav();
}

// 依「本地時區」格式化成 YYYY-MM-DD；不要用 toISOString().slice(0,10)，
// 那是轉成 UTC 後才截字串，在 UTC+8 會把日期往前拉一天
function toLocalDateString(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// 檢查目前登入狀態，回傳 user 物件或 null；供各頁面判斷要不要導去登入頁
async function getCurrentUser() {
  try {
    return await api.get("/api/auth/me");
  } catch (e) {
    return null;
  }
}

// 右側浮動社群 icon + 回頂部按鈕，比照 volunfittc.com.tw 的做法，所有
// 頁面共用同一份（position:fixed 不需要放在特定 HTML 位置，直接掛到
// document.body 尾端即可）。連結目前都是佔位用的 #，等有真實的
// LINE/FB/IG 帳號再換掉 href。
function renderFloatingExtras() {
  const dock = document.createElement("div");
  dock.className = "floating-dock";
  dock.innerHTML = `
    <a href="#" class="dock-icon dock-line" title="LINE">💬</a>
    <a href="#" class="dock-icon dock-fb" title="Facebook">📘</a>
    <a href="#" class="dock-icon dock-ig" title="Instagram">📷</a>
    <a href="/book.html" class="dock-icon dock-book" title="立即預約">📅</a>
  `;
  document.body.appendChild(dock);

  const topBtn = document.createElement("button");
  topBtn.type = "button";
  topBtn.className = "back-to-top";
  topBtn.textContent = "↑ TOP";
  topBtn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  document.body.appendChild(topBtn);

  const toggleTopBtn = () => topBtn.classList.toggle("show", window.scrollY > 400);
  window.addEventListener("scroll", toggleTopBtn, { passive: true });
  toggleTopBtn();
}

document.addEventListener("DOMContentLoaded", renderNav);
document.addEventListener("DOMContentLoaded", renderFloatingExtras);
