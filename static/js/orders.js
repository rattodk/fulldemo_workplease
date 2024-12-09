// static/js/orders.js
document.addEventListener("DOMContentLoaded", function () {
  // Filter buttons functionality
  const filterButtons = document.querySelectorAll(".filter-btn");
  const orderCards = document.querySelectorAll(".order-card");

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      // Update active button
      filterButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");

      // Filter orders
      const status = button.dataset.status;
      orderCards.forEach((card) => {
        if (status === "all" || card.dataset.status === status) {
          card.style.display = "block";
        } else {
          card.style.display = "none";
        }
      });
    });
  });
});

// Update order status
async function updateOrderStatus(orderId) {
  const statusSelect = document.getElementById(`status-${orderId}`);
  const newStatus = statusSelect.value;

  try {
    const response = await fetch(`/api/orders/${orderId}/status`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status: newStatus,
        order_pk: orderId,
      }),
    });

    if (response.ok) {
      // Update UI
      const orderCard = statusSelect.closest(".order-card");
      orderCard.dataset.status = newStatus;
      const statusBadge = orderCard.querySelector(".status-badge");
      statusBadge.className = `status-badge ${newStatus}`;
      statusBadge.textContent =
        newStatus.charAt(0).toUpperCase() + newStatus.slice(1);

      // Show success message
      alert("Order status updated successfully");
    } else {
      throw new Error("Failed to update order status");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Failed to update order status");
  }
}
