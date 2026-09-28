const STATUS_LABEL = {
  pending: "待審核",
  approved: "已核准",
  rejected: "已拒絕",
};

async function loadRequests() {
  const status = document.getElementById("status-filter").value;
  const url = status ? `/api/admin/bookings?status=${status}` : "/api/admin/bookings";
  const requests = await api.get(url);
  const tbody = document.getElementById("request-list");
  if (requests.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8">沒有符合的申請</td></tr>';
    return;
  }
  tbody.innerHTML = requests
    .map((r) => {
      const actions =
        r.status === "pending"
          ? `<button data-action="approve" data-id="${r.id}">核准</button>
             <button class="secondary" data-action="reject" data-id="${r.id}">拒絕</button>`
          : "";
      const errorHint = r.sync_error
        ? `<div class="error-text">建立課程失敗：${r.sync_error.replace(/</g, "&lt;")}</div>`
        : "";
      return `
        <tr>
          <td>${r.user_name || ""}</td>
          <td>${r.slot.date}</td>
          <td>${r.slot.start_time.slice(0, 5)}</td>
          <td>${r.slot.venue_name}</td>
          <td>${r.slot.session_type_name}</td>
          <td>${r.student_note ? r.student_note.replace(/</g, "&lt;") : ""}</td>
          <td><span class="status-${r.status}">${STATUS_LABEL[r.status] || r.status}</span>${errorHint}</td>
          <td>${actions}</td>
        </tr>`;
    })
    .join("");
}

document.getElementById("status-filter").addEventListener("change", loadRequests);

document.getElementById("request-list").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const id = btn.dataset.id;
  const errorEl = document.getElementById("action-error");
  errorEl.style.display = "none";
  try {
    if (btn.dataset.action === "approve") {
      await api.post(`/api/admin/bookings/${id}/approve`, {});
    } else if (btn.dataset.action === "reject") {
      if (!(await confirmDialog("確定要拒絕這筆申請嗎？"))) return;
      await api.post(`/api/admin/bookings/${id}/reject`, {});
    }
  } catch (err) {
    errorEl.textContent = "操作失敗：" + err.message;
    errorEl.style.display = "";
  }
  await loadRequests();
});

document.addEventListener("DOMContentLoaded", loadRequests);
