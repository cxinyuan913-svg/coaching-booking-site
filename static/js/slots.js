// 月曆選日期 + 當天時段列表（Calendly 風格）。開放時段通常不多，一次把
// 全部開放時段抓回來、在前端依日期分組，不用另外做伺服器端分月查詢。

let slotsByDate = {}; // { "2026-11-02": [slot, ...] }
let currentUser = null;
let currentMonth = null; // Date，day 固定為 1
let selectedDate = null; // "YYYY-MM-DD"
let selectedSlotId = null;

function groupSlotsByDate(slots) {
  const map = {};
  slots.forEach((slot) => {
    if (!map[slot.date]) map[slot.date] = [];
    map[slot.date].push(slot);
  });
  Object.values(map).forEach((list) => list.sort((a, b) => a.start_time.localeCompare(b.start_time)));
  return map;
}

function renderCalendar() {
  const grid = document.getElementById("calendar-grid");
  const title = document.getElementById("cal-title");
  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  title.textContent = `${year}年${month + 1}月`;

  const firstWeekday = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const todayStr = toLocalDateString(new Date());

  grid.innerHTML = "";
  for (let i = 0; i < firstWeekday; i++) {
    const empty = document.createElement("div");
    empty.className = "calendar-day empty";
    grid.appendChild(empty);
  }
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = toLocalDateString(new Date(year, month, day));
    const hasSlots = !!slotsByDate[dateStr];
    const isPast = dateStr < todayStr;
    const cell = document.createElement("div");
    cell.className = "calendar-day";
    if (isPast) cell.classList.add("past");
    if (hasSlots && !isPast) cell.classList.add("has-slots");
    if (dateStr === selectedDate) cell.classList.add("selected");
    cell.innerHTML = `${day}${hasSlots && !isPast ? '<span class="slot-dot"></span>' : ""}`;
    if (hasSlots && !isPast) {
      cell.addEventListener("click", () => selectDate(dateStr));
    }
    grid.appendChild(cell);
  }
}

function selectDate(dateStr) {
  selectedDate = dateStr;
  renderCalendar();
  renderDaySlots();
}

function renderDaySlots() {
  const section = document.getElementById("day-slots-section");
  const title = document.getElementById("day-slots-title");
  const list = document.getElementById("day-slots-list");
  const slots = slotsByDate[selectedDate] || [];

  section.style.display = "";
  title.textContent = `${selectedDate} 的開放時段`;
  list.innerHTML = slots
    .map(
      (slot) => `
        <button type="button" class="slot-chip" data-id="${slot.id}">
          ${slot.start_time.slice(0, 5)}　${slot.venue_name}　${slot.session_type_name}
        </button>`
    )
    .join("");
}

async function loadSlots() {
  const slots = await api.get("/api/slots");
  slotsByDate = groupSlotsByDate(slots);

  if (Object.keys(slotsByDate).length === 0) {
    document.getElementById("no-slots-hint").style.display = "";
    document.querySelector(".calendar-card").style.display = "none";
    return;
  }

  // 預設把月曆跳到「最早有開放時段的那個月」，避免打開頁面剛好是空月份
  const earliestDate = Object.keys(slotsByDate).sort()[0];
  const [y, m] = earliestDate.split("-").map(Number);
  currentMonth = new Date(y, m - 1, 1);
  renderCalendar();
}

function formatSlotSummary(slot) {
  return `${slot.date} ${slot.start_time.slice(0, 5)}（${slot.venue_name}，${slot.session_type_name}）`;
}

function openBookingModal(slotId) {
  const slot = (slotsByDate[selectedDate] || []).find((s) => s.id === slotId);
  if (!slot) return;
  selectedSlotId = slotId;
  document.getElementById("booking-slot-summary").textContent = formatSlotSummary(slot);
  document.getElementById("f-note").value = "";
  document.getElementById("booking-error").style.display = "none";
  document.getElementById("booking-modal").classList.add("open");
}

function closeBookingModal() {
  document.getElementById("booking-modal").classList.remove("open");
  selectedSlotId = null;
}

async function submitBooking() {
  const errorEl = document.getElementById("booking-error");
  errorEl.style.display = "none";
  try {
    await api.post("/api/bookings", {
      slot_id: selectedSlotId,
      student_note: document.getElementById("f-note").value.trim() || null,
    });
    closeBookingModal();
    document.getElementById("booking-success-banner").style.display = "";
    await loadSlots();
    if (selectedDate && slotsByDate[selectedDate]) {
      renderDaySlots();
    } else {
      document.getElementById("day-slots-section").style.display = "none";
    }
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "";
  }
}

document.getElementById("day-slots-list").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-id]");
  if (!btn) return;
  if (!currentUser) {
    window.location.href = "/login.html";
    return;
  }
  openBookingModal(parseInt(btn.dataset.id, 10));
});

document.getElementById("cal-prev").addEventListener("click", () => {
  currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
  renderCalendar();
});

document.getElementById("cal-next").addEventListener("click", () => {
  currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
  renderCalendar();
});

document.getElementById("btn-cancel-booking").addEventListener("click", closeBookingModal);
document.getElementById("btn-submit-booking").addEventListener("click", submitBooking);

document.addEventListener("DOMContentLoaded", async () => {
  currentUser = await getCurrentUser();
  await loadSlots();
});
