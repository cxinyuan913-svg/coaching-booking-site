document.getElementById("register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorText = document.getElementById("error-text");
  errorText.style.display = "none";
  try {
    await api.post("/api/auth/register", {
      name: document.getElementById("f-name").value.trim(),
      email: document.getElementById("f-email").value.trim(),
      phone: document.getElementById("f-phone").value.trim() || null,
      password: document.getElementById("f-password").value,
    });
    window.location.href = "/";
  } catch (err) {
    errorText.textContent = err.message;
    errorText.style.display = "";
  }
});
