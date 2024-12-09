// Make Cart available globally
window.Cart = class Cart {
  constructor() {
    this.items = JSON.parse(localStorage.getItem("cart")) || {};
    this.syncTimeout = null;
    this.deliveryFee = 29; // Fixed delivery fee
  }

  addItem(restaurantId, item) {
    if (!restaurantId || !item || !item.item_pk) {
      console.error("Invalid item data:", { restaurantId, item });
      return false;
    }

    const currentRestaurantId = this.getRestaurantId();
    if (currentRestaurantId && currentRestaurantId !== restaurantId) {
      if (
        !confirm(
          "Adding items from a different restaurant will clear your current cart. Continue?"
        )
      ) {
        return false;
      }
      this.clearCart();
    }

    const cartItem = {
      restaurantId,
      itemId: item.item_pk,
      name: item.item_name,
      price: parseFloat(item.item_price),
      quantity: 1,
    };

    if (this.items[item.item_pk]) {
      this.items[item.item_pk].quantity += 1;
    } else {
      this.items[item.item_pk] = cartItem;
    }

    this.saveCart();
    this.updateCartDisplay();

    // Show cart after adding item
    const cartSidebar = document.getElementById("cartSidebar");
    if (cartSidebar) {
      cartSidebar.style.display = "block";
      this.renderCartSidebar();
    }
    return true;
  }

  removeItem(itemId) {
    if (this.items[itemId]) {
      delete this.items[itemId];
      this.saveCart();
      this.updateCartDisplay();
    }
  }

  updateQuantity(itemId, quantity) {
    if (!this.items[itemId]) return;

    if (quantity < 1) {
      this.removeItem(itemId);
      return;
    }

    this.items[itemId].quantity = quantity;
    this.saveCart();
    this.updateCartDisplay();
  }

  getRestaurantId() {
    const firstItem = Object.values(this.items)[0];
    return firstItem ? firstItem.restaurantId : null;
  }

  getTotal() {
    const itemTotal = Object.values(this.items).reduce((total, item) => {
      return total + item.price * item.quantity;
    }, 0);
    return itemTotal + this.deliveryFee;
  }

  clearCart() {
    this.items = {};
    localStorage.removeItem("cart");
    this.saveCart();
    this.updateCartDisplay();
  }

  saveCart() {
    try {
      localStorage.setItem("cart", JSON.stringify(this.items));
      if (this.syncTimeout) {
        clearTimeout(this.syncTimeout);
      }
      this.syncTimeout = setTimeout(() => {
        this.syncWithServer();
      }, 500);
    } catch (error) {
      console.error("Failed to save cart:", error);
    }
  }

  async syncWithServer() {
    try {
      const response = await fetch("/api/save-cart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.items),
      });

      if (!response.ok) {
        throw new Error("Failed to sync cart with server");
      }
    } catch (error) {
      console.error("Error syncing cart with server:", error);
    }
  }

  updateCartDisplay() {
    const cartCount = Object.values(this.items).reduce(
      (count, item) => count + item.quantity,
      0
    );
    const cartCountElement = document.getElementById("cartCount");
    if (cartCountElement) {
      cartCountElement.textContent = cartCount || "";
      cartCountElement.style.display = cartCount ? "flex" : "none";
    }

    const cartSidebar = document.getElementById("cartSidebar");
    if (cartSidebar && cartSidebar.style.display !== "none") {
      this.renderCartSidebar();
    }
  }

  renderCartSidebar() {
    const cartContent = document.getElementById("cartContent");
    const cartSidebar = document.getElementById("cartSidebar");
    if (!cartContent || !cartSidebar) return;

    if (Object.keys(this.items).length === 0) {
      cartSidebar.style.display = "none";
      return;
    }

    cartSidebar.style.display = "block";
    cartContent.innerHTML = `
      <div class="cart-items">
        ${Object.values(this.items)
          .map(
            (item) => `
          <div class="cart-item">
            <div class="cart-item-info">
              <h4>${this.escapeHtml(item.name)}</h4>
              <p class="price">$${(item.price * item.quantity).toFixed(2)}</p>
            </div>
            <div class="cart-item-quantity">
              <button 
                onclick="cart.updateQuantity('${item.itemId}', ${
              item.quantity - 1
            })"
                class="btn btn-small"
                aria-label="Decrease quantity"
              >-</button>
              <span>${item.quantity}</span>
              <button 
                onclick="cart.updateQuantity('${item.itemId}', ${
              item.quantity + 1
            })"
                class="btn btn-small"
                aria-label="Increase quantity"
              >+</button>
            </div>
          </div>
        `
          )
          .join("")}
      </div>
      <div class="cart-total">
        <p>Delivery Fee: $${this.deliveryFee.toFixed(2)}</p>
        <h3>Total: $${this.getTotal().toFixed(2)}</h3>
        <button 
          onclick="cart.checkout()"
          class="btn gradient checkout-button"
        >
          Checkout
        </button>
      </div>
      <div class="cart-sidebar-footer">
        <button 
          onclick="cart.toggleCart()"
          class="btn btn-secondary close-cart-button"
        >
          Close
        </button>
      </div>`;
  }

  toggleCart() {
    const cartSidebar = document.getElementById("cartSidebar");
    if (!cartSidebar) return;

    const isVisible = cartSidebar.style.display === "block";

    if (Object.keys(this.items).length === 0 && isVisible) {
      cartSidebar.style.display = "none";
      return;
    }

    cartSidebar.style.display = isVisible ? "none" : "block";

    if (!isVisible) {
      this.renderCartSidebar();
    }
  }

  escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  checkout() {
    if (Object.keys(this.items).length === 0) {
      alert("Your cart is empty!");
      return;
    }

    this.syncWithServer().then(() => {
      window.location.href = "/checkout";
    });
  }
};

// Initialize cart when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  // Initialize cart
  window.cart = new Cart();

  // Add click handler for cart icon
  const cartIcon = document.querySelector(".cart-icon");
  if (cartIcon) {
    cartIcon.addEventListener("click", () => window.cart.toggleCart());
  }

  // Initial cart display update
  window.cart.updateCartDisplay();
});

// Make cart toggle function available globally
window.toggleCartSidebar = function () {
  if (window.cart) {
    window.cart.toggleCart();
  }
};
