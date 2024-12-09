document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("searchRestaurantsAndDishes");

  if (!searchInput) {
    console.error("Search input not found in the DOM.");
    return;
  }

  searchInput.addEventListener("input", filterRestaurantsAndDishes);

  function filterRestaurantsAndDishes() {
    const query = searchInput.value.toLowerCase();
    const restaurantCards = document.querySelectorAll(".restaurant-card");

    restaurantCards.forEach((card) => {
      // Extract the restaurant name and address
      const restaurantName = card.querySelector("h3").textContent.toLowerCase();
      const restaurantAddress = card
        .querySelector("p")
        .textContent.toLowerCase();

      // Find all menu items under the restaurant card
      const menuContent = card.querySelector(".menu-content");
      const menuItems = menuContent
        ? menuContent.querySelectorAll(".menu-item")
        : [];

      let restaurantMatch =
        restaurantName.includes(query) || restaurantAddress.includes(query);
      let dishMatch = false;

      // Check for matching menu items
      menuItems.forEach((item) => {
        const dishName = item.textContent.toLowerCase();
        if (dishName.includes(query)) {
          dishMatch = true;
          item.style.display = ""; // Show matching dishes
        } else {
          item.style.display = "none"; // Hide non-matching dishes
        }
      });

      // Show or hide restaurant card based on matches
      card.style.display = restaurantMatch || dishMatch ? "" : "none";

      // Reset all dishes' visibility if the restaurant itself matches
      if (restaurantMatch) {
        menuItems.forEach((item) => {
          item.style.display = ""; // Ensure all dishes are visible
        });
      }
    });
  }
});
