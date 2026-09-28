document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorText = document.getElementById("error-text");
  errorText.style.display = "none";
  try {
    const user = await api.post("/api/auth/login", {
      email: document.getElementById("f-email").value.trim(),
      password: document.getElementById("f-password").value,
    });
    window.location.href = user.is_coach ? "/admin_requests.html" : "/";
  } catch (err) {
    errorText.textContent = err.message;
    errorText.style.display = "";
  }
});
