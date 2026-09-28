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

async function loadSessionTypes() {
  sessionTypes = await api.get("/api/admin/session_types");
  document.getElementById("session-type-list").innerHTML = sessionTypes
    .map((s) => `<tr><td>${s.name}</td><td>${s.duration_minutes}</td><td>${s.reference_price}</td></tr>`)
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
  await api.post("/api/admin/session_types", {
    name: document.getElementById("st-name").value.trim(),
    duration_minutes: parseInt(document.getElementById("st-duration").value, 10),
    reference_price: parseFloat(document.getElementById("st-price").value),
  });
  document.getElementById("session-type-form").reset();
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
