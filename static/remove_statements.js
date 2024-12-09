// Client-side input sanitization
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("input").forEach((input) => {
    input.addEventListener("input", function (e) {
      // Remove any SQL injection attempts
      this.value = this.value.replace(/['";]/g, "");

      // Remove any HTML tags
      this.value = this.value.replace(/<[^>]*>/g, "");

      // Remove multiple spaces
      this.value = this.value.replace(/\s\s+/g, " ");
    });
  });
});
