const STATUS_LABEL = {
  pending: "審核中",
  approved: "已核准",
  rejected: "已拒絕",
};

async function loadMyBookings() {
  const tbody = document.getElementById("booking-list");
  let bookings;
  try {
    bookings = await api.get("/api/bookings");
  } catch (err) {
    window.location.href = "/login.html";
    return;
  }
  if (bookings.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">還沒有送出過預約申請</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  bookings.forEach((b) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${b.slot.date}</td>
      <td>${b.slot.start_time.slice(0, 5)}</td>
      <td>${b.slot.venue_name}</td>
      <td>${b.slot.session_type_name}</td>
      <td><span class="status-${b.status}">${STATUS_LABEL[b.status] || b.status}</span></td>
      <td>${b.student_note ? b.student_note.replace(/</g, "&lt;") : ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

document.addEventListener("DOMContentLoaded", loadMyBookings);
