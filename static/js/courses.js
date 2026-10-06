// 課程介紹頁：課程卡片抓 GET /api/courses 動態渲染（教練在後台編輯），不寫死 HTML。
function renderCourseCard(course) {
  const priceText = course.reference_price > 0 ? `NT$ ${Math.round(course.reference_price)}` : "";
  return `
    <div class="card course-card">
      <span class="eyebrow">${course.duration_minutes} 分鐘</span>
      <h3>${escapeHtml(course.name)}</h3>
      ${course.target_audience ? `<p class="course-card-meta">適合：${escapeHtml(course.target_audience)}</p>` : ""}
      <p>${escapeHtml(course.description)}</p>
      ${priceText ? `<div class="course-card-price">${priceText}</div>` : ""}
    </div>
  `;
}

async function loadCourses() {
  const grid = document.getElementById("course-grid");
  if (!grid) return;
  try {
    const courses = await api.get("/api/courses");
    if (courses.length === 0) {
      grid.innerHTML = '<p style="color: var(--ink-3)">課程項目準備中，請直接洽詢教練。</p>';
      return;
    }
    grid.innerHTML = courses.map(renderCourseCard).join("");
  } catch (err) {
    grid.innerHTML = '<p class="error-text">課程資料載入失敗，請稍後再試。</p>';
  }
}

document.addEventListener("DOMContentLoaded", loadCourses);
