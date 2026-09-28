// 共用 fetch 工具與導覽列渲染

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

// 置中的確認視窗，取代原生 confirm()（原生 confirm/alert 會整個鎖住分頁，
// 沒辦法用程式化方式關掉，一律避免使用，見 CLAUDE.md 的開發慣例）
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

const BADMINTON_LOGO_SVG = `
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 3 L3 12 L7 21 L21 7 Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
    <path d="M12 3 L21 7 M3 12 L7 21 M12 3 L7 21 M3 12 L21 7" stroke="currentColor" stroke-width="0.7" opacity="0.6"/>
    <circle cx="17" cy="17" r="2.4" fill="currentColor"/>
  </svg>
`;

// 行銷網站導覽列（首頁那套設計）：左 logo、中間錨點選單、右邊預約按鈕，
// 手機版收成漢堡選單。錨點一律用 /#id 的絕對路徑，不管使用者現在在哪個
// 頁面點都會先跳回首頁、捲到對應區塊，不用每頁各自判斷路徑。
function renderMarketingNav(nav, user) {
  nav.innerHTML = `
    <div class="nav-inner">
      <a href="/" class="nav-logo">
        ${BADMINTON_LOGO_SVG}
        <span class="nav-logo-text">
          <strong>Raymond 羽球教室</strong>
          <small>BADMINTON COACHING</small>
        </span>
      </a>
      <button type="button" class="nav-hamburger" aria-label="開啟選單">☰</button>
      <div class="nav-menu" id="nav-menu">
        <a href="/#about">關於教練<span class="nav-en">About</span></a>
        <a href="/#course">課程介紹<span class="nav-en">Course</span></a>
        <a href="/#process">上課流程<span class="nav-en">Process</span></a>
        <a href="/#venue">上課場地<span class="nav-en">Venue</span></a>
        <a href="/#faq">常見問題<span class="nav-en">FAQ</span></a>
        ${user ? '<a href="/my_bookings.html">我的預約</a><a href="#" id="nav-logout">登出</a>' : ""}
        <a href="/book.html" class="btn btn-primary nav-cta-mobile">預約體驗<span class="nav-en">Booking</span></a>
      </div>
      <a href="/book.html" class="btn btn-primary nav-cta">預約體驗<span class="nav-en">Booking</span></a>
    </div>
  `;

  nav.querySelector(".nav-hamburger").addEventListener("click", () => {
    nav.querySelector(".nav-menu").classList.toggle("open");
  });

  const logout = nav.querySelector("#nav-logout");
  if (logout) {
    logout.addEventListener("click", async (e) => {
      e.preventDefault();
      await api.post("/api/auth/logout", null).catch(() => {});
      window.location.href = "/login.html";
    });
  }
}

// 教練後台用的簡易導覽列：維持原本「一排文字連結」的精簡風格
function renderSimpleNav(nav, user) {
  const links = [
    ["/", "首頁"],
    ["/admin_slots.html", "開放時段管理"],
    ["/admin_requests.html", "審核申請"],
  ];
  nav.innerHTML = `<div class="nav-simple">${links
    .map(([href, label]) => `<a href="${href}">${label}</a>`)
    .join("")}<a href="#" id="nav-logout">登出</a></div>`;

  nav.querySelector("#nav-logout").addEventListener("click", async (e) => {
    e.preventDefault();
    await api.post("/api/auth/logout", null).catch(() => {});
    window.location.href = "/login.html";
  });
}

// 依登入狀態決定導覽列長怎樣：教練看到後台的簡易導覽列；其他人（不管
// 有沒有登入）看到行銷網站那套 logo+錨點選單+預約按鈕的導覽列。
async function renderNav() {
  const nav = document.getElementById("topnav");
  if (!nav) return;
  const user = await getCurrentUser();

  if (user && user.is_coach) {
    renderSimpleNav(nav, user);
  } else {
    renderMarketingNav(nav, user);
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

document.addEventListener("DOMContentLoaded", renderNav);
