let venues = [];
let sessionTypes = [];
let generatedDates = [];

async function loadVenues() {
  venues = await api.get("/api/admin/venues");
  document.getElementById("venue-list").innerHTML = venues
    .map((v) => `<tr><td>${v.name}</td><td>${v.address || ""}</td></tr>`)
    .join("");
  const select = document.getElementById("batch-venue");
  select.innerHTML = venues.map((v) => `<option value="${v.id}">${v.name}</option>`).join("");
}

// 說明/適合對象是自由輸入的文字，塞進 innerHTML 前先跳脫，打了 < 之類的字元不會壞版
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}

async function loadSessionTypes() {
  sessionTypes = await api.get("/api/admin/session_types");
  document.getElementById("session-type-list").innerHTML = sessionTypes
    .map(
      (s) => `<tr>
        <td>${escapeHtml(s.name)}</td>
        <td>${s.duration_minutes}</td>
        <td>${s.reference_price}</td>
        <td style="white-space: pre-line">${escapeHtml(s.description) || "—"}</td>
        <td>${escapeHtml(s.target_audience) || "—"}</td>
        <td><button type="button" class="secondary" data-edit-session-type="${s.id}">編輯</button></td>
      </tr>`
    )
    .join("");
  const select = document.getElementById("batch-session-type");
  select.innerHTML = sessionTypes.map((s) => `<option value="${s.id}">${s.name}</option>`).join("");
}

async function loadSlots() {
  const slots = await api.get("/api/admin/slots");
  const tbody = document.getElementById("slot-list");
  if (slots.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">還沒有開放任何時段</td></tr>';
    return;
  }
  tbody.innerHTML = slots
    .map(
      (s) => `
        <tr>
          <td>${s.date}</td>
          <td>${s.start_time.slice(0, 5)}</td>
          <td>${s.venue_name}</td>
          <td>${s.session_type_name}</td>
          <td>${s.is_booked ? "已被約走" : "開放中"}</td>
          <td>${s.is_booked ? "" : `<button class="danger" data-id="${s.id}">刪除</button>`}</td>
        </tr>`
    )
    .join("");
}

document.getElementById("venue-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  await api.post("/api/admin/venues", {
    name: document.getElementById("venue-name").value.trim(),
    address: document.getElementById("venue-address").value.trim() || null,
  });
  document.getElementById("venue-form").reset();
  await loadVenues();
});

document.getElementById("session-type-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("st-create-error");
  errorEl.style.display = "none";
  try {
    await api.post("/api/admin/session_types", {
      name: document.getElementById("st-name").value.trim(),
      duration_minutes: parseInt(document.getElementById("st-duration").value, 10),
      reference_price: parseFloat(document.getElementById("st-price").value),
      description: document.getElementById("st-description").value.trim() || null,
      target_audience: document.getElementById("st-audience").value.trim() || null,
    });
  } catch (err) {
    errorEl.textContent = `新增失敗：${err.message}`;
    errorEl.style.display = "";
    return;
  }
  document.getElementById("session-type-form").reset();
  await loadSessionTypes();
});

// ---------- 編輯課程 ----------

const editForm = document.getElementById("session-type-edit-form");

function openSessionTypeEditor(id) {
  const s = sessionTypes.find((item) => item.id === id);
  if (!s) return;
  document.getElementById("st-edit-id").value = s.id;
  document.getElementById("st-edit-name").value = s.name;
  document.getElementById("st-edit-duration").value = s.duration_minutes;
  document.getElementById("st-edit-price").value = s.reference_price;
  document.getElementById("st-edit-audience").value = s.target_audience || "";
  document.getElementById("st-edit-description").value = s.description || "";
  document.getElementById("st-edit-error").style.display = "none";
  editForm.style.display = "";
  editForm.scrollIntoView({ behavior: "smooth", block: "nearest" });
  document.getElementById("st-edit-name").focus();
}

document.getElementById("session-type-list").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-edit-session-type]");
  if (btn) openSessionTypeEditor(parseInt(btn.dataset.editSessionType, 10));
});

document.getElementById("btn-st-edit-cancel").addEventListener("click", () => {
  editForm.style.display = "none";
});

editForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("st-edit-error");
  errorEl.style.display = "none";
  const id = document.getElementById("st-edit-id").value;
  try {
    await api.patch(`/api/admin/session_types/${id}`, {
      name: document.getElementById("st-edit-name").value.trim(),
      duration_minutes: parseInt(document.getElementById("st-edit-duration").value, 10),
      reference_price: parseFloat(document.getElementById("st-edit-price").value),
      // 清空就送 null，讓首頁卡片不再顯示這一行
      description: document.getElementById("st-edit-description").value.trim() || null,
      target_audience: document.getElementById("st-edit-audience").value.trim() || null,
    });
  } catch (err) {
    errorEl.textContent = `儲存失敗：${err.message}`;
    errorEl.style.display = "";
    return;
  }
  editForm.style.display = "none";
  await loadSessionTypes();
});

document.getElementById("btn-generate-dates").addEventListener("click", () => {
  const errorEl = document.getElementById("batch-error");
  errorEl.style.display = "none";
  const startStr = document.getElementById("batch-start-date").value;
  if (!startStr) {
    errorEl.textContent = "請先選起始日期";
    errorEl.style.display = "";
    return;
  }
  const interval = parseInt(document.getElementById("batch-interval").value, 10);
  const count = parseInt(document.getElementById("batch-count").value, 10);
  const [y, m, d] = startStr.split("-").map(Number);
  const start = new Date(y, m - 1, d);

  generatedDates = [];
  for (let i = 0; i < count; i++) {
    const dt = new Date(start);
    dt.setDate(dt.getDate() + i * interval);
    generatedDates.push(toLocalDateString(dt));
  }

  const container = document.getElementById("date-checkboxes");
  container.innerHTML = generatedDates
    .map(
      (dateStr) => `
        <label style="display: inline-block; margin: 4px 12px 4px 0">
          <input type="checkbox" checked data-date="${dateStr}" /> ${dateStr}
        </label>`
    )
    .join("");
  document.getElementById("btn-submit-batch").style.display = "";
});

document.getElementById("btn-submit-batch").addEventListener("click", async () => {
  const errorEl = document.getElementById("batch-error");
  errorEl.style.display = "none";
  const checked = Array.from(document.querySelectorAll("#date-checkboxes input:checked")).map(
    (el) => el.dataset.date
  );
  if (checked.length === 0) {
    errorEl.textContent = "至少要留一個日期";
    errorEl.style.display = "";
    return;
  }
  try {
    await api.post("/api/admin/slots", {
      venue_id: parseInt(document.getElementById("batch-venue").value, 10),
      session_type_id: parseInt(document.getElementById("batch-session-type").value, 10),
      dates: checked,
      start_time: document.getElementById("batch-start-time").value + ":00",
    });
    document.getElementById("date-checkboxes").innerHTML = "";
    document.getElementById("btn-submit-batch").style.display = "none";
    await loadSlots();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "";
  }
});

document.getElementById("slot-list").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-id]");
  if (!btn) return;
  if (!(await confirmDialog("確定要刪除這個時段嗎？"))) return;
  await api.delete(`/api/admin/slots/${btn.dataset.id}`);
  await loadSlots();
});

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([loadVenues(), loadSessionTypes(), loadSlots()]);
});
