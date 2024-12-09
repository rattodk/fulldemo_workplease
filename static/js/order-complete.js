// Attach the onsubmit event handler to the checkout form
document.getElementById("checkoutForm").onsubmit = async function (event) {
  event.preventDefault(); // Prevent the default form submission behavior

  const formData = new FormData(this); // Collect all form data
  const submitButton = document.querySelector(".btn.gradient"); // Get the submit button
  submitButton.textContent = "Processing...";
  submitButton.disabled = true;

  try {
    // Send the form data to the backend
    const response = await fetch("/place-order", {
      method: "POST",
      body: formData,
    });

    // Parse the response as JSON
    const result = await response.json();

    if (result.success) {
      // Clear the cart after a successful order
      clearCart();

      // Redirect to the order completion page
      window.location.href = result.redirect_url;
    } else {
      // Handle errors returned by the backend
      alert(result.message || "Failed to place order. Please try again.");
    }
  } catch (error) {
    // Catch any unexpected errors during the fetch process
    console.error("Error placing order:", error);
    alert("An error occurred while placing your order. Please try again.");
  } finally {
    // Reset the button state regardless of success or failure
    submitButton.textContent = "Place Order";
    submitButton.disabled = false;
  }
};

// Utility function to clear the cart and update the UI
function clearCart() {
  // Clear the cart from local storage
  localStorage.removeItem("cart");

  // Update the cart display to show it's empty
  const cartContent = document.getElementById("cartContent");
  if (cartContent) {
    cartContent.innerHTML = "<p>Your cart is empty.</p>";
  }

  const cartTotal = document.querySelector(".cart-total h3");
  if (cartTotal) {
    cartTotal.textContent = "Total: $0.00";
  }
}

// Optional: Logic for resetting the cart when the page loads
document.addEventListener("DOMContentLoaded", () => {
  // Placeholder for any additional logic when the page loads
});
