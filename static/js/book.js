// 四步驟預約精靈：選課程 → 選日期（一週7格） → 選時段（格狀三態） → 聯絡資料。
// 沿用既有 AvailabilitySlot 資料（GET /api/slots 只回傳「還沒被訂走、日期還沒過」
// 的時段），只是把呈現方式從月曆改成這種 Calendly 風格的分步卡片。
//
// 時段格是「固定時間格 + 對照真實開放時段」：平日顯示 17-22 這幾個整點、
// 假日顯示 9-16 這幾個整點，每格如果剛好有對應的開放時段就能點（可預約／
// 已選），沒有對應時段的格子顯示成「已額滿」（劃線、不能點）——教練是手動
// 開時段，不是固定每天都開，所以「這格沒開」跟「這格滿了」對學生來說
// 是同一種結果：不能約，用同一種視覺呈現。

const WEEKDAY_LABELS = ["日", "一", "二", "三", "四", "五", "六"];
const WEEKDAY_HOURS = [17, 18, 19, 20, 21, 22];
const WEEKEND_HOURS = [9, 10, 11, 13, 14, 15];

let courses = [];
let slotsByDate = {}; // { "2026-11-02": [slot, ...] }
let currentUser = null;
let weekStart = startOfWeek(new Date());
let selectedCourseId = null;
let selectedDate = null; // "YYYY-MM-DD"
let selectedSlot = null; // slot 物件本身，不只是 id，摘要卡直接用它的欄位

function startOfWeek(d) {
  const date = new Date(d);
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day; // 週一為一週開頭
  date.setDate(date.getDate() + diff);
  date.setHours(0, 0, 0, 0);
  return date;
}

function candidateHoursForDate(dateStr) {
  const day = new Date(`${dateStr}T00:00:00`).getDay();
  return day === 0 || day === 6 ? WEEKEND_HOURS : WEEKDAY_HOURS;
}

function groupSlotsByDate(slots) {
  const map = {};
  slots.forEach((slot) => {
    if (!map[slot.date]) map[slot.date] = [];
    map[slot.date].push(slot);
  });
  return map;
}

/* ---------- Step 1：選課程 ---------- */
function renderCourseSelect() {
  const grid = document.getElementById("course-select-grid");
  if (courses.length === 0) {
    grid.innerHTML = '<p style="color: var(--ink-3)">目前沒有開放課程，請直接聯絡教練。</p>';
    return;
  }
  grid.innerHTML = courses
    .map(
      (c) => `
        <button type="button" class="course-select-card ${c.id === selectedCourseId ? "selected" : ""}" data-id="${c.id}">
          <h4>${c.name}</h4>
          <p>${c.duration_minutes} 分鐘${c.reference_price > 0 ? `・NT$ ${Math.round(c.reference_price)}` : ""}</p>
        </button>`
    )
    .join("");
  grid.querySelectorAll("button[data-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedCourseId = parseInt(btn.dataset.id, 10);
      selectedSlot = null;
      renderCourseSelect();
      renderSlotGrid();
      updateSummary();
    });
  });
}

/* ---------- Step 2：選日期（一週 7 格） ---------- */
function renderWeekStrip() {
  const container = document.getElementById("date-week-days");
  const todayStr = toLocalDateString(new Date());
  container.innerHTML = "";
  for (let i = 0; i < 7; i++) {
    const d = new Date(weekStart);
    d.setDate(weekStart.getDate() + i);
    const dateStr = toLocalDateString(d);
    const isPast = dateStr < todayStr;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "date-day-cell";
    btn.disabled = isPast;
    if (dateStr === selectedDate) btn.classList.add("selected");
    btn.innerHTML = `<span class="dow">${WEEKDAY_LABELS[d.getDay()]}</span><span class="dom">${d.getDate()}</span>`;
    if (!isPast) {
      btn.addEventListener("click", () => {
        selectedDate = dateStr;
        selectedSlot = null;
        renderWeekStrip();
        renderSlotGrid();
        updateSummary();
      });
    }
    container.appendChild(btn);
  }
}

document.getElementById("week-prev").addEventListener("click", () => {
  const prevWeek = new Date(weekStart);
  prevWeek.setDate(weekStart.getDate() - 7);
  if (prevWeek < startOfWeek(new Date())) return; // 不能翻到今天所在週之前
  weekStart = prevWeek;
  renderWeekStrip();
});

document.getElementById("week-next").addEventListener("click", () => {
  weekStart = new Date(weekStart.getFullYear(), weekStart.getMonth(), weekStart.getDate() + 7);
  renderWeekStrip();
});

/* ---------- Step 3：選時段（格狀三態） ---------- */
function renderSlotGrid() {
  const grid = document.getElementById("slot-time-grid");
  const hint = document.getElementById("slot-time-hint");
  grid.innerHTML = "";

  if (!selectedCourseId || !selectedDate) {
    hint.style.display = "";
    hint.textContent = "請先選課程與日期";
    return;
  }

  const daySlots = (slotsByDate[selectedDate] || []).filter((s) => s.session_type_id === selectedCourseId);
  hint.style.display = daySlots.length === 0 ? "" : "none";
  hint.textContent = "這天這個課程沒有開放時段，試試其他日期";

  candidateHoursForDate(selectedDate).forEach((hour) => {
    const label = `${String(hour).padStart(2, "0")}:00`;
    const slot = daySlots.find((s) => s.start_time.slice(0, 5) === label);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "slot-time-cell";
    btn.textContent = label;
    if (!slot) {
      btn.classList.add("full");
      btn.disabled = true;
    } else {
      if (selectedSlot && selectedSlot.id === slot.id) btn.classList.add("selected");
      btn.addEventListener("click", () => {
        selectedSlot = slot;
        renderSlotGrid();
        updateSummary();
      });
    }
    grid.appendChild(btn);
  });
}

/* ---------- 右側明細卡 ---------- */
function setSummaryValue(id, value) {
  const el = document.getElementById(id);
  el.textContent = value || "尚未選擇";
  el.classList.toggle("placeholder", !value);
}

function updateSummary() {
  const course = courses.find((c) => c.id === selectedCourseId);
  setSummaryValue("summary-course", course ? course.name : null);
  setSummaryValue("summary-date", selectedDate);
  setSummaryValue("summary-time", selectedSlot ? selectedSlot.start_time.slice(0, 5) : null);
  setSummaryValue("summary-venue", selectedSlot ? selectedSlot.venue_name : null);
  document.getElementById("summary-price").textContent =
    course && course.reference_price > 0 ? `NT$ ${Math.round(course.reference_price)}` : "--";
  document.getElementById("btn-submit-booking").disabled = !selectedSlot;
}

/* ---------- 送出申請 ---------- */
async function submitBooking() {
  const errorEl = document.getElementById("booking-error");
  errorEl.style.display = "none";

  if (!currentUser) {
    window.location.href = "/login.html";
    return;
  }
  if (!selectedSlot) return;

  try {
    await api.post("/api/bookings", {
      slot_id: selectedSlot.id,
      student_note: document.getElementById("f-note").value.trim() || null,
      student_level: document.getElementById("f-level").value || null,
      focus_note: document.getElementById("f-focus").value.trim() || null,
    });
    document.getElementById("booking-form-wrap").style.display = "none";
    document.getElementById("booking-success").style.display = "";
    await loadSlots();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "";
  }
}

document.getElementById("btn-submit-booking").addEventListener("click", submitBooking);

document.getElementById("btn-book-again").addEventListener("click", () => {
  selectedCourseId = null;
  selectedDate = null;
  selectedSlot = null;
  weekStart = startOfWeek(new Date());
  document.getElementById("f-level").value = "";
  document.getElementById("f-focus").value = "";
  document.getElementById("f-note").value = "";
  renderCourseSelect();
  renderWeekStrip();
  renderSlotGrid();
  updateSummary();
  document.getElementById("booking-success").style.display = "none";
  document.getElementById("booking-form-wrap").style.display = "";
});

/* ---------- 初始載入 ---------- */
async function loadCourses() {
  courses = await api.get("/api/courses");
  renderCourseSelect();
}

async function loadSlots() {
  const slots = await api.get("/api/slots");
  slotsByDate = groupSlotsByDate(slots);
  renderSlotGrid();
}

document.addEventListener("DOMContentLoaded", async () => {
  currentUser = await getCurrentUser();
  renderWeekStrip();
  updateSummary();
  await Promise.all([loadCourses(), loadSlots()]);
});
