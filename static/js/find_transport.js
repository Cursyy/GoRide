let currentStation = null;
let activeController = null;
let routeLayer = null;
let map = null;
let price = null;
let voucher = false;
const vehiclesPerPage = 10;
let currentPage = 1;
let allVehicles = [];
let baseLayer = null;
let initialTilesLoaded = false;
let allStationsData = [];

document.addEventListener("DOMContentLoaded", function () {
  if (document.getElementById("map")) {
    loadStations();
  }
  if (document.getElementById("vehicle-container")) {
    loadVehicles();
  }

  const batteryFilter = document.getElementById("battery-filter");
  const typeFilter = document.getElementById("type-filter");

  if (batteryFilter && typeFilter) {
    batteryFilter.addEventListener("input", function () {
      const batteryDisplay = document.getElementById("battery-display");
      if (batteryDisplay) {
        batteryDisplay.textContent = `${this.value}%`;
      }
      loadVehicles(currentStation);
    });

    typeFilter.addEventListener("change", function () {
      loadVehicles(currentStation);
    });
  } else {
  }
});

document.addEventListener("submit", async function (event) {
  if (!event.target.matches(".voucher-form")) return;

  event.preventDefault();

  const form = event.target;
  const vehicleId = form.getAttribute("data-vehicle-id");
  const voucherCode = form.querySelector("input[name='voucher']").value;
  const voucherType = form.querySelector("input[name='voucher_type']").value;

  try {
    const response = await fetch(`api/voucher`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({
        vehicle_id: vehicleId,
        code: voucherCode,
        type: voucherType,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      alert(`Voucher applied successfully. New price: €${data.price}`);
      price = data.price;
      voucher = true;
    } else {
      alert(`Error: ${data.error}`);
    }
  } catch (error) {
    alert("Something went wrong while applying the voucher. Please try again.");
  }
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function initializeMap() {
  map = L.map("map");

  baseLayer = L.tileLayer(
    "https://maps.geoapify.com/v1/tile/klokantech-basic/{z}/{x}/{y}.png?apiKey=d16fda76e6fc4822bbc407474c620a8e",
    {
      attribution:
        'Powered by <a href="https://www.geoapify.com/" target="_blank">Geoapify</a> | <a href="https://openmaptiles.org/" target="_blank">© OpenMapTiles</a> <a href="https://www.openstreetmap.org/copyright" target="_blank">© OpenStreetMap</a> contributors',
      maxZoom: 20,
      id: "osm-bright",
    },
  );

  baseLayer.once("load", function () {
    initialTilesLoaded = true;
    showPosition();
    addStationMarkers(allStationsData);
  });

  baseLayer.addTo(map);

  if (window.GLOBAL_USER_LOCATION_AVAILABLE) {
    map.setView(
      [window.GLOBAL_USER_LATITUDE, window.GLOBAL_USER_LONGITUDE],
      15,
    );
  } else {
    map.setView([53.347854, -6.259504], 13);
  }
}

function showPosition() {
  if (!initialTilesLoaded || !map) {
    return;
  }
  if (window.GLOBAL_USER_LOCATION_AVAILABLE) {
    let userIcon = L.icon({
      iconUrl: "/static/images/you_are_here.png",
      iconSize: [38, 50],
      iconAnchor: [22, 38],
      popupAnchor: [-3, -38],
    });
    L.marker([window.GLOBAL_USER_LATITUDE, window.GLOBAL_USER_LONGITUDE], {
      icon: userIcon,
    })
      .bindPopup("You are here")
      .openPopup()
      .addTo(map);
  }
}

async function loadStations() {
  try {
    const response = await fetch("api/stations");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    allStationsData = await response.json();
    initializeMap();
  } catch (error) {
    console.error("Error loading stations:", error);
    initializeMap();
  }
}

function addStationMarkers(stations) {
  if (!initialTilesLoaded || !map) {
    return;
  }
  stations.forEach((station) => {
    let stationIcon = L.icon({
      iconUrl: "/static/images/map-marker-2-64.png",
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    });
    let marker = L.marker([station.latitude, station.longitude], {
      icon: stationIcon,
    })
      .bindPopup(
        `<b>Max spaces:</b> ${station.max_spaces}<br><b>Free spaces:</b> ${station.free_spaces}<br>${station.address}`,
      )
      .addTo(map);
    marker.on("click", function () {
      currentStation = station.id;
      loadVehicles(station.id);
      createButton(station.id);
    });
  });
}

async function loadVehicles(stationId = null) {
  try {
    const response = await fetch("api/vehicles");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    let fetchedVehicles = await response.json();

    const typeFilterValue = document.getElementById("type-filter")
      ? document.getElementById("type-filter").value
      : "";
    const batteryFilterValue = document.getElementById("battery-filter")
      ? parseInt(document.getElementById("battery-filter").value)
      : 0;

    if (stationId) {
      allVehicles = fetchedVehicles.filter(
        (v) =>
          v.station_id === stationId &&
          (typeFilterValue === "" || v.type === typeFilterValue) &&
          (v.battery_percentage === null ||
            v.battery_percentage >= batteryFilterValue),
      );
    } else {
      allVehicles = fetchedVehicles.filter(
        (v) =>
          (typeFilterValue === "" || v.type === typeFilterValue) &&
          (v.battery_percentage === null ||
            v.battery_percentage >= batteryFilterValue),
      );
    }

    currentPage = 1;
    displayVehicles();
    setupPagination();
  } catch (error) {
    console.error("Error loading vehicles:", error);
    const container = document.getElementById("vehicle-container");
    if (container) {
      container.innerHTML =
        "<p>Error loading vehicles. Please try again later.</p>";
    }
  }
}

function displayVehicles() {
  const container = document.getElementById("vehicle-container");
  if (!container) return;
  container.innerHTML = "";

  const start = (currentPage - 1) * vehiclesPerPage;
  const end = start + vehiclesPerPage;
  const vehiclesToShow = allVehicles.slice(start, end);

  if (vehiclesToShow.length === 0) {
    container.innerHTML = "<p>No vehicles match the current criteria.</p>";
    const paginationContainer = document.getElementById("pagination-controls");
    if (paginationContainer) paginationContainer.innerHTML = "";
    return;
  }

  vehiclesToShow.forEach((vehicle) => {
    const vehicleCard = document.createElement("div");
    vehicleCard.classList.add("vehicle-card");

    let imgSrc;
    switch (vehicle.type) {
      case "Bike":
        imgSrc = "/static/images/bike.webp";
        break;
      case "E-Bike":
        imgSrc = "/static/images/e-bike.jpg";
        break;
      case "E-Scooter":
        imgSrc = "/static/images/e-scooter.jpg";
        break;
      default:
        imgSrc = "/static/images/placeholder.jpg";
    }
    const mapLink =
      vehicle.latitude != null && vehicle.longitude != null
        ? `<a href="https://www.google.com/maps/search/?api=1&query=${vehicle.latitude},${vehicle.longitude}"
                 target="_blank" class="map-link">Show on Map</a>`
        : `<span class="map-link-na">Map N/A</span>`; // Or empty string

    vehicleCard.innerHTML = `
            <div class="vehicle-image">
                <img src="${imgSrc}" alt="${vehicle.type || "Vehicle"} image"/>
            </div>
            <div class="vehicle-details">
                <h3>${vehicle.type || "Unknown Type"}</h3>
                ${
                  vehicle.battery_percentage !== null
                    ? `<p>Battery: ${vehicle.battery_percentage}%</p>`
                    : "<p>Battery: N/A</p>"
                }
                ${mapLink}
            </div>
            <div class="vehicle-price">
                <p>Price per hour: €${
                  vehicle.price_per_hour != null
                    ? vehicle.price_per_hour.toFixed(2)
                    : "N/A"
                }</p>
                <a href="/booking/rent/${
                  vehicle.id
                }/" class="rent-button w-100 text-center">Rent</a>
            </div>`;

    container.appendChild(vehicleCard);
  });
}

function setupPagination() {
  const pageNumbersContainer = document.getElementById("page-numbers");
  const prevButton = document.getElementById("prev-page");
  const nextButton = document.getElementById("next-page");

  if (!pageNumbersContainer || !prevButton || !nextButton) {
    return;
  }

  const totalPages = Math.ceil(allVehicles.length / vehiclesPerPage);
  const paginationContainer = document.getElementById("pagination-controls");
  if (paginationContainer) {
    paginationContainer.style.display = totalPages <= 1 ? "none" : "";
  }
  if (totalPages <= 1) {
    pageNumbersContainer.innerHTML = "";
    prevButton.style.display = "none";
    nextButton.style.display = "none";
    return;
  } else {
    prevButton.style.display = "";
    nextButton.style.display = "";
  }

  pageNumbersContainer.innerHTML = "";

  const maxVisiblePages = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
  let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

  if (endPage - startPage + 1 < maxVisiblePages) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1);
  }

  for (let i = startPage; i <= endPage; i++) {
    const pageButton = document.createElement("button");
    pageButton.innerText = i;
    pageButton.classList.add("page-button", "mx-1");

    if (i === currentPage) {
      pageButton.classList.add("active");
      pageButton.disabled = true;
    }

    pageButton.addEventListener("click", () => {
      currentPage = i;
      displayVehicles();
      setupPagination();
    });

    pageNumbersContainer.appendChild(pageButton);
  }

  prevButton.disabled = currentPage === 1;
  nextButton.disabled = currentPage === totalPages;

  const newPrevButton = prevButton.cloneNode(true);
  prevButton.parentNode.replaceChild(newPrevButton, prevButton);
  newPrevButton.disabled = currentPage === 1;
  newPrevButton.addEventListener("click", () => {
    if (currentPage > 1) {
      currentPage--;
      displayVehicles();
      setupPagination();
    }
  });

  const newNextButton = nextButton.cloneNode(true);
  nextButton.parentNode.replaceChild(newNextButton, nextButton);
  newNextButton.disabled = currentPage === totalPages;
  newNextButton.addEventListener("click", () => {
    if (currentPage < totalPages) {
      currentPage++;
      displayVehicles();
      setupPagination();
    }
  });
}

function createButton() {
  let button = document.getElementById("get-direction-button");
  const buttonContainer = document.getElementById("map");

  if (currentStation === null || !buttonContainer) {
    if (button) button.remove();
  }

  if (!button) {
    button = document.createElement("button");
    button.id = "get-direction-button";
    button.textContent = "Get Directions";
    button.classList.add("direction-button-style");
    buttonContainer.appendChild(button);
  }

  const newButton = button.cloneNode(true);
  button.parentNode.replaceChild(newButton, button);

  newButton.addEventListener("click", function () {
    getDirection(currentStation);
  });
}

async function getDirection(stationId = null) {
  if (stationId === null || !window.GLOBAL_USER_LOCATION_AVAILABLE) {
    alert("Please select a station and ensure location is enabled.");
    return;
  }
  try {
    if (activeController) {
      activeController.abort();
    }
    activeController = new AbortController();
    const commonSignal = activeController.signal;

    const stationResponse = await fetch(`api/stations?id=${stationId}`, {
      signal: commonSignal,
    });
    if (!stationResponse.ok) {
      if (stationResponse.status === 404)
        throw new Error("Selected station not found.");
      throw new Error(
        `Error fetching station details: ${stationResponse.statusText}`,
      );
    }
    const stationData = await stationResponse.json();
    const station = stationData.station;

    if (!station || station.latitude == null || station.longitude == null) {
      throw new Error("Invalid station data received.");
    }

    const directionResponse = await fetch(
      `api/get_direction/${station.id}/${window.GLOBAL_USER_LONGITUDE}/${window.GLOBAL_USER_LATITUDE}`,
      { signal: commonSignal },
    );
    if (!directionResponse.ok) {
      throw new Error(
        `Error fetching directions: ${directionResponse.statusText}`,
      );
    }
    const directionData = await directionResponse.json();

    if (
      !directionData.features ||
      !directionData.features[0] ||
      !directionData.features[0].geometry ||
      !directionData.features[0].geometry.coordinates
    ) {
      throw new Error("Invalid direction data format received.");
    }

    const coordinates = directionData.features[0].geometry.coordinates;
    drawRouteOnMap(coordinates);
  } catch (error) {
    if (error.name === "AbortError") {
    } else {
      console.error("Error in getDirection:", error);
      alert(`Could not get directions: ${error.message}`);
    }
  } finally {
    activeController = null;
  }
}

function drawRouteOnMap(coordinates) {
  if (!map) return;

  if (routeLayer) {
    map.removeLayer(routeLayer);
  }
  const latLngs = coordinates.map((coord) => [coord[1], coord[0]]);
  if (latLngs.length === 0) return;
  routeLayer = L.polyline(latLngs, { color: "blue", weight: 5 });
  routeLayer.addTo(map);
  map.fitBounds(routeLayer.getBounds().pad(0.1));
}
