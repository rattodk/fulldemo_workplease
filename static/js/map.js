document.addEventListener("DOMContentLoaded", () => {
  const mapContainer = document.getElementById("map");
  const toggleMapButton = document.getElementById("toggleMap");
  let mapInitialized = false;

  if (!toggleMapButton) {
    console.error("Toggle Map button not found in the DOM.");
    return;
  }

  if (!mapContainer) {
    console.error("Map container (div#map) not found in the DOM.");
    return;
  }

  // Add a click event listener to the toggle button
  toggleMapButton.addEventListener("click", () => {
    console.log("Map View button clicked.");

    if (
      mapContainer.style.display === "none" ||
      mapContainer.style.display === ""
    ) {
      console.log("Toggling map: showing the map.");
      mapContainer.style.display = "block"; // Show the map
      mapContainer.style.height = "400px"; // Ensure height is set

      if (!mapInitialized) {
        console.log("Map not initialized. Initializing map...");
        try {
          setTimeout(() => initializeMap(), 100); // Ensure container is visible before initialization
          mapInitialized = true;
          console.log("Map initialized successfully.");
        } catch (error) {
          console.error("Error during map initialization:", error);
        }
      } else {
        console.log("Map already initialized.");
      }
    } else {
      console.log("Toggling map: hiding the map.");
      mapContainer.style.display = "none"; // Hide the map
    }
  });

  /**
   * Initializes the map using Leaflet.
   */
  function initializeMap() {
    console.log("Starting Leaflet map initialization...");

    // Create the Leaflet map instance
    const map = L.map("map").setView([0, 0], 2); // Default view to the world
    console.log("Leaflet map instance created.");

    // Add OpenStreetMap tile layer
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
    }).addTo(map);
    console.log("Tile layer added to map.");

    // Fetch random restaurants from the API
    fetch("/api/random-restaurants")
      .then((response) => {
        console.log("API request sent to /api/random-restaurants.");
        if (!response.ok) {
          throw new Error(`API response error: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log("API response received:", data);

        const { restaurants } = data;
        if (restaurants.length === 0) {
          console.warn("No restaurants found in API response.");
          return;
        }

        // Center the map to the first restaurant's location
        const [firstRestaurant] = restaurants;
        map.setView([firstRestaurant.latitude, firstRestaurant.longitude], 13);
        console.log(
          `Map centered to first restaurant at [${firstRestaurant.latitude}, ${firstRestaurant.longitude}].`
        );

        // Add markers for each restaurant
        restaurants.forEach((restaurant) => {
          console.log(
            `Adding marker for restaurant: ${restaurant.name}, [${restaurant.latitude}, ${restaurant.longitude}]`
          );
          const marker = L.marker([
            restaurant.latitude,
            restaurant.longitude,
          ]).addTo(map);

          // Bind a popup to the marker
          marker.bindPopup(`
            <b>${restaurant.name}</b><br>
            ${restaurant.address}<br>
            <button 
              class="btn btn-primary mt-2" 
              onclick="handleMarkerMenuClick('${restaurant.restaurant_id}')">
              View Menu
            </button>
          `);
        });

        console.log("All restaurant markers added to the map.");
      })
      .catch((error) => {
        console.error("Error fetching or processing API response:", error);
      });
  }

  /**
   * Handles marker click to simulate a menu button click.
   * @param {string} restaurantId - The unique ID of the restaurant.
   */
  function handleMarkerMenuClick(restaurantId) {
    console.log(`Marker clicked for restaurant ID: ${restaurantId}`);

    if (!restaurantId) {
      console.error("Restaurant ID is not provided.");
      return;
    }

    const menuButton = document.getElementById(`btn-${restaurantId}`);
    if (!menuButton) {
      console.error(`Menu button for restaurant ID ${restaurantId} not found.`);
      return;
    }

    console.log(
      `Simulating click on menu button for restaurant ID: ${restaurantId}`
    );
    menuButton.click(); // Simulate a click on the menu button
  }
});
