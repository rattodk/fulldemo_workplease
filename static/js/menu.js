/**
 * menu.js - Handles dynamic loading and display of restaurant menus
 */

// Utility function to safely escape HTML content
function escapeHtml(unsafe) {
  if (!unsafe) return "";
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Main function to handle loading and displaying restaurant menus
async function loadMenu(restaurantId, event) {
  if (!restaurantId) {
    console.error("No restaurant ID provided");
    return;
  }

  const menuDiv = document.getElementById(`menu-${restaurantId}`);
  const button = document.getElementById(`btn-${restaurantId}`);
  const grid = document.getElementById("restaurantGrid");

  if (!menuDiv || !button || !grid) {
    console.error("Required DOM elements not found");
    return;
  }

  // Close other open menus
  const allMenus = document.querySelectorAll(".menu-items");
  const allButtons = document.querySelectorAll('[id^="btn-"]');
  allMenus.forEach((menu) => {
    const menuId = menu.id.replace("menu-", "");
    if (menuId !== restaurantId) {
      menu.style.display = "none";
      const btn = document.getElementById(`btn-${menuId}`);
      if (btn) btn.textContent = "View Menu";
    }
  });

  const isLoaded = button.getAttribute("data-loaded") === "true";
  const isMenuVisible = menuDiv.style.display === "block";

  if (!isMenuVisible) {
    // Reposition menu in grid
    menuDiv.remove();
    const computedStyle = window.getComputedStyle(grid);
    const columns = computedStyle.gridTemplateColumns.split(" ").length;
    const cards = Array.from(grid.children);
    const clickedCard = button.closest(".restaurant-card");
    const cardIndex = cards.indexOf(clickedCard);
    const currentRow = Math.floor(cardIndex / columns);

    const nextRowIndex = (currentRow + 1) * columns;
    if (nextRowIndex < cards.length) {
      grid.insertBefore(menuDiv, cards[nextRowIndex]);
    } else {
      grid.appendChild(menuDiv);
    }

    menuDiv.style.display = "block";
    button.textContent = "Hide Menu";
    menuDiv.style.gridColumn = "1 / -1";

    if (!isLoaded) {
      await loadMenuContent(restaurantId, menuDiv, button);
    }
  } else {
    menuDiv.style.display = "none";
    button.textContent = "View Menu";
  }
}

// Fetches and renders menu content from the server
async function loadMenuContent(restaurantId, menuDiv, button) {
  const menuContent = menuDiv.querySelector(".menu-content");
  if (!menuContent) {
    console.error("Menu content container not found");
    return;
  }

  menuContent.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Loading menu...</p>
    </div>`;

  try {
    const response = await fetch(`/api/menu/${restaurantId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    renderMenuItems(data, menuContent, restaurantId);
    button.setAttribute("data-loaded", "true");
  } catch (error) {
    console.error("Error loading menu:", error);
    menuContent.innerHTML = `
      <div class="error-state">
        <p>Error loading menu items. Please try again.</p>
        <button onclick="loadMenu('${restaurantId}')" class="btn btn-secondary">
          Retry
        </button>
      </div>`;
  }
}

// Renders the menu items grouped by category
function renderMenuItems(data, menuContent, restaurantId) {
  if (!data.menu_items || data.menu_items.length === 0) {
    menuContent.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <iconify-icon icon="material-symbols:restaurant-menu" width="48" height="48"></iconify-icon>
        </div>
        <p>No menu items available for this restaurant yet.</p>
      </div>`;
    return;
  }

  // Group items by category
  const itemsByCategory = data.menu_items.reduce((acc, item) => {
    const category = item.item_category || "Uncategorized";
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push({ ...item, restaurant_id: restaurantId });
    return acc;
  }, {});

  menuContent.innerHTML = `
    <div class="menu-categories">
      ${Object.entries(itemsByCategory)
        .map(
          ([category, items]) => `
          <div class="menu-category">
            <h3 class="category-title">${escapeHtml(category)}</h3>
            <div class="menu-grid">
              ${items.map((item) => renderMenuItem(item)).join("")}
            </div>
          </div>`
        )
        .join("")}
    </div>`;
}

// Renders a single menu item
function renderMenuItem(item) {
  const isAvailable = item.item_available !== 0;
  let imageUrl = "/static/images/default-placeholder.png";

  // Handle different image data formats
  if (Array.isArray(item.item_images) && item.item_images.length > 0) {
    imageUrl = item.item_images[0];
  } else if (
    typeof item.item_images === "string" &&
    item.item_images.trim() !== ""
  ) {
    imageUrl = item.item_images.split(",")[0];
  }

  return `
    <div class="menu-item p-3 border rounded">
      <div class="menu-item-image">
        <img
          src="${imageUrl}"
          alt="${escapeHtml(item.item_name)}"
          class="dish-image"
          onerror="this.onerror=null; this.src='/static/images/default-placeholder.png';"
        />
      </div>
      <h4>${escapeHtml(item.item_name)}</h4>
      <p class="item-description">${escapeHtml(item.item_description || "")}</p>
      <div class="menu-item-footer">
        <p class="price">$${parseFloat(item.item_price).toFixed(2)}</p>
        <button 
          onclick="addToCart('${item.restaurant_id}', ${JSON.stringify(
    item
  ).replace(/"/g, "&quot;")})"
          class="add-to-cart-btn btn btn-primary"
          ${!isAvailable ? "disabled" : ""}
        >
          ${isAvailable ? "Add to Cart" : "Out of Stock"}
        </button>
      </div>
    </div>`;
}

// Function to add items to cart
function addToCart(restaurantId, item) {
  try {
    if (!window.cart) {
      console.error("Cart not initialized");
      alert("Unable to add item to cart. Please try refreshing the page.");
      return;
    }

    const success = window.cart.addItem(restaurantId, item);
    if (success) {
      // Optional: Show a success message
      const toast = document.createElement("div");
      toast.className = "toast success";
      toast.textContent = "Item added to cart";
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 2000);
    }
  } catch (error) {
    console.error("Error adding item to cart:", error);
    alert("Failed to add item to cart. Please try again.");
  }
}

// Initialize event listeners when the document is ready
document.addEventListener("DOMContentLoaded", () => {
  // Add any additional initialization here if needed
  console.log("Menu.js initialized");
});
