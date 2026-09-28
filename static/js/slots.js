let currentUser = null;
let selectedSlotId = null;

function formatSlot(slot) {
  return `${slot.date} ${slot.start_time.slice(0, 5)}（${slot.venue_name}，${slot.session_type_name}）`;
}

async function loadSlots() {
  const tbody = document.getElementById("slot-list");
  const slots = await api.get("/api/slots");
  if (slots.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">目前沒有開放的時段</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  slots.forEach((slot) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${slot.date}</td>
      <td>${slot.start_time.slice(0, 5)}</td>
      <td>${slot.venue_name}</td>
      <td>${slot.session_type_name}（${slot.duration_minutes}分鐘）</td>
      <td>參考 $${slot.reference_price}</td>
      <td><button data-id="${slot.id}" data-summary="${formatSlot(slot)}">預約</button></td>
    `;
    tbody.appendChild(tr);
  });
}

function openBookingModal(slotId, summary) {
  selectedSlotId = slotId;
  document.getElementById("booking-slot-summary").textContent = summary;
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
    // 用原生 alert() 會整個鎖住分頁、不能用工具或程式化方式關掉，一律
    // 避免使用（見 coaching-record-tool 的 common.js 為什麼自己刻
    // confirmDialog 取代原生 confirm() 的同樣理由）
    document.getElementById("booking-success-banner").style.display = "";
    await loadSlots();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "";
  }
}

document.getElementById("slot-list").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-id]");
  if (!btn) return;
  if (!currentUser) {
    window.location.href = "/login.html";
    return;
  }
  openBookingModal(parseInt(btn.dataset.id, 10), btn.dataset.summary);
});

document.getElementById("btn-cancel-booking").addEventListener("click", closeBookingModal);
document.getElementById("btn-submit-booking").addEventListener("click", submitBooking);

document.addEventListener("DOMContentLoaded", async () => {
  currentUser = await getCurrentUser();
  await loadSlots();
});
