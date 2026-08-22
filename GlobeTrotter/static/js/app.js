document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("input[type=date]").forEach(el => {
    if (!el.min) el.min = "2020-01-01";
  });
  document.querySelectorAll("form").forEach(form => {
    form.addEventListener("submit", () => {
      const btn = form.querySelector("button[type=submit], button:not(.btn-close)");
      if (btn && !form.dataset.confirmed) {
        btn.dataset.original = btn.innerHTML;
        // Prevent accidental double submissions.
        setTimeout(() => { btn.disabled = true; }, 0);
      }
    });
  });
});