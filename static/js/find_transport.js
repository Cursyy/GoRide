let currentStation = null;
let activeController = null;
let routeLayer = null;
let map = null;
let price = null;
const vehiclesPerPage = 10;
let currentPage = 1;
let allVehicles = [];
let baseLayer = null;
let initialTilesLoaded = false;
let allStationsData = [];
let currentVehicle = null;
let stationClusterGroup = null;
let vehicleClusterGroup = null;
let clickTimeout = null;

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
  if (map) return;

  map = L.map("map", {
    doubleClickZoom: false,
  });

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
    if (document.getElementById("vehicle-container")) {
      loadVehicles();
    }
  });

  baseLayer.addTo(map);
  stationClusterGroup = L.markerClusterGroup();
  vehicleClusterGroup = L.markerClusterGroup({
    maxClusterRadius: 160,
  });
  map.addLayer(stationClusterGroup);
  map.addLayer(vehicleClusterGroup);
  if (window.GLOBAL_USER_LOCATION_AVAILABLE) {
    map.setView(
      [window.GLOBAL_USER_LATITUDE, window.GLOBAL_USER_LONGITUDE],
      15,
    );
  } else {
    map.setView([53.347854, -6.259504], 13);
  }
  map.on("click", function (e) {
    clickTimeout = setTimeout(() => {
      console.log("Single click");
      if (currentStation !== null || currentVehicle !== null) {
        currentStation = null;
        currentVehicle = null;
        loadVehicles();
        createButton();
      }
    }, 250);
  });

  map.on("dblclick", function (e) {
    console.log("Double click");
    currentStation = null;
    currentVehicle = null;
    if (routeLayer && map.hasLayer(routeLayer)) {
      map.removeLayer(routeLayer);
      routeLayer = null;
    }
    if (clickTimeout) {
      clearTimeout(clickTimeout);
      clickTimeout = null;
    }
  });
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
  stationClusterGroup.clearLayers();
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
    stationClusterGroup.addLayer(marker);
    marker.on("click", function () {
      currentStation = station.id;
      currentVehicle = null;
      loadVehicles(station.id);
      createButton();
    });
  });
}

async function loadVehicles(stationId = null) {
  try {
    console.log(`Loading vehicles. Station ID: ${stationId}`);
    const response = await fetch("api/vehicles");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    let fetchedVehicles = await response.json();
    console.log(`Workspaceed ${fetchedVehicles.length} vehicles total.`);

    const typeFilterValue = document.getElementById("type-filter")?.value || "";
    const batteryFilterValue = parseInt(
      document.getElementById("battery-filter")?.value || "0",
    );

    let baseFilteredVehicles = fetchedVehicles.filter((v) => {
      const matchType = !typeFilterValue || v.type === typeFilterValue;
      const matchBattery =
        v.battery_percentage === null ||
        v.battery_percentage >= batteryFilterValue;
      return matchType && matchBattery;
    });
    console.log(
      `${baseFilteredVehicles.length} vehicles after type/battery filter.`,
    );

    displayVehiclesMap(baseFilteredVehicles);
    console.log("Called displayVehiclesMap.");

    if (stationId !== null) {
      console.log(`Filtering list for station ${stationId}`);
      allVehicles = baseFilteredVehicles.filter(
        (v) => v.station_id === stationId,
      );
    } else {
      console.log(
        "Filtering list for free-floating vehicles (no station selected).",
      );
      allVehicles = baseFilteredVehicles.filter((v) => v.station_id === null);
    }
    console.log(
      `${allVehicles.length} vehicles prepared for the list display.`,
    );

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
function displayVehiclesMap(vehiclesToDisplay) {
  if (!initialTilesLoaded || !map) {
    console.error("Map or tiles haven't loaded yet for displayVehiclesMap");
    return;
  }
  vehicleClusterGroup.clearLayers();
  if (window.vehicleMarkersLayer && map.hasLayer(window.vehicleMarkersLayer)) {
    window.vehicleMarkersLayer.clearLayers();
  } else {
    window.vehicleMarkersLayer = L.layerGroup().addTo(map);
  }

  let displayedCount = 0;
  vehiclesToDisplay.forEach((vehicle) => {
    if (vehicle.station_id !== null) return;

    if (vehicle.latitude != null && vehicle.longitude != null) {
      displayedCount++;
      let iconUrl;
      switch (vehicle.type) {
        case "Bike":
          iconUrl = "/static/images/bike.webp";
          break;
        case "E-Bike":
          iconUrl = "/static/images/e-bike.jpg";
          break;
        case "E-Scooter":
          iconUrl = "/static/images/e-scooter.jpg";
          break;
      }

      let vehicleIcon = L.divIcon({
        html: `<div style="width: 32px; height: 32px; background-image: url('${iconUrl}'); background-size: cover; border-radius: 50%;"></div>`,
        className: "",
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32],
      });

      let marker = L.marker([vehicle.latitude, vehicle.longitude], {
        icon: vehicleIcon,
      })
        .bindPopup(function () {
          switch (vehicle.type) {
            case "Bike":
              return `<b>Type:</b> ${vehicle.type}`;
            default:
              return `<b>Battery charge:</b> ${
                vehicle.battery_percentage !== null
                  ? vehicle.battery_percentage + "%"
                  : "N/A"
              }<br><b>Type:</b> ${vehicle.type}`;
          }
        })
        .addTo(window.vehicleMarkersLayer);
      vehicleClusterGroup.addLayer(marker);
      marker.on("click", function () {
        currentVehicle = vehicle.id;
        currentStation = null;
        createButton();
      });
    }
  });
  console.log(
    `Displayed ${displayedCount} free-floating vehicle markers on map.`,
  );
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
    vehicleCard.classList.add("vehicle-card", "mb-4");

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
    const mapLink = (function () {
      if (vehicle.station_id === null) {
        return vehicle.latitude != null && vehicle.longitude != null
          ? `<button onclick="focusOnVehicle(${vehicle.latitude}, ${vehicle.longitude})" class="map-link btn btn-sm btn-outline-primary">Show on Map</button>`
          : `<span class="map-link-na text-muted">Map N/A</span>`;
      } else {
        const station = allStationsData.find(
          (station) => station.id === vehicle.station_id,
        );
        return vehicle.latitude != null && vehicle.longitude != null
          ? `<button onclick="focusOnVehicle(${station.latitude}, ${station.longitude})" class="map-link btn btn-sm btn-outline-primary">Show on Map</button>`
          : `<span class="map-link-na text-muted">Map N/A</span>`;
      }
    })();

    vehicleCard.innerHTML = `
            <div class="vehicle-image">
                <img src="${imgSrc}" alt="${
                  vehicle.type || "Vehicle"
                } image" style="width: 106%; height: auto;"/>             </div>
            <div class="vehicle-details">
                <h3>${vehicle.type || "Unknown Type"}</h3>
                ${(function () {
                  switch (vehicle.type) {
                    case "Bike":
                      return "";
                    default:
                      return vehicle.battery_percentage !== null
                        ? `<p>Battery: ${vehicle.battery_percentage}%</p>`
                        : "<p>Battery: N/A</p>";
                  }
                })()}
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
                }/" class="rent-button btn btn-success w-100 text-center">Rent</a>             </div>`;

    container.appendChild(vehicleCard);
  });
}
function focusOnVehicle(lat, lon) {
  if (map && lat != null && lon != null && vehicleClusterGroup) {
    map.setView([lat, lon], 17);

    vehicleClusterGroup.zoomToShowLayer(L.latLng(lat, lon), function () {
      vehicleClusterGroup.eachLayer((marker) => {
        const markerLatLng = marker.getLatLng();
        if (markerLatLng.lat === lat && markerLatLng.lng === lon) {
          setTimeout(() => {
            marker.openPopup();
          }, 100);
        }
      });
    });
  } else {
    console.warn(
      "Map, coordinates, or vehicleClusterGroup not ready for focus.",
    );
  }
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

  if (!buttonContainer) {
    console.error("Button container ('map') not found.");
    return;
  }

  if (currentStation === null && currentVehicle === null) {
    if (button) {
      button.remove();
    }
    return;
  }

  if (!button) {
    button = document.createElement("button");
    button.id = "get-direction-button";
    button.textContent = "Get Directions";
    button.classList.add("direction-button-style", "btn", "btn-primary");
    button.style.position = "absolute";
    button.style.top = "10px";
    button.style.right = "10px";
    button.style.zIndex = "1000";
    buttonContainer.appendChild(button);
  }

  const newButton = button.cloneNode(true);
  button.parentNode.replaceChild(newButton, button);

  newButton.addEventListener("click", function () {
    const stationTarget = currentStation;
    const vehicleTarget = currentVehicle;
    getDirection(stationTarget, vehicleTarget);
  });
}

async function getDirection(targetStationId, targetVehicleId) {
  if (
    (targetStationId === null && targetVehicleId === null) ||
    !window.GLOBAL_USER_LOCATION_AVAILABLE
  ) {
    alert(
      "Please select a station or vehicle first, and ensure location is enabled.",
    );
    return;
  }

  let request_id = null;
  let type = null;
  if (targetVehicleId !== null) {
    request_id = targetVehicleId;
    type = "vehicle";
    console.log(`Routing to vehicle ID: ${request_id}`);
  } else if (targetStationId !== null) {
    request_id = targetStationId;
    type = "station";
    console.log(`Routing to station ID: ${request_id}`);
  } else {
    console.error(
      "No target ID found in getDirection, though button was clicked.",
    );
    return;
  }

  if (activeController) {
    console.log("Aborting previous direction request.");
    activeController.abort();
  }

  const currentAbortController = new AbortController();
  const commonSignal = currentAbortController.signal;

  activeController = currentAbortController;

  try {
    await apiRespond(request_id, type, commonSignal);
  } catch (error) {
    if (error.name === "AbortError") {
      console.log(
        "Direction request process (getDirection level) was aborted.",
      );
    } else {
      console.error("Error in getDirection process:", error);
      alert(`Could not get directions: ${error.message}`);
      if (routeLayer && map.hasLayer(routeLayer)) {
        map.removeLayer(routeLayer);
        routeLayer = null;
      }
    }
  }
}

async function apiRespond(request_id, type, commonSignal) {
  try {
    if (commonSignal.aborted) {
      console.log("API request aborted before fetch.");
      return;
    }

    const directionResponse = await fetch(
      `api/get_direction/${request_id}/${window.GLOBAL_USER_LONGITUDE}/${window.GLOBAL_USER_LATITUDE}/${type}`,
      { signal: commonSignal },
    );
    if (!directionResponse.ok) {
      throw new Error(
        `Error fetching directions (${directionResponse.status}): ${directionResponse.statusText}`,
      );
    }
    const directionData = await directionResponse.json();

    if (
      !directionData.features ||
      !directionData.features[0] ||
      !directionData.features[0].geometry ||
      !directionData.features[0].geometry.coordinates
    ) {
      throw new Error("Invalid direction data format received from API.");
    }

    const coordinates = directionData.features[0].geometry.coordinates;
    drawRouteOnMap(coordinates);
  } catch (error) {
    if (error.name === "AbortError") {
      console.log("API fetch/process aborted.");
    } else {
      console.error("Error during API response/processing:", error);
      alert(`Could not process directions: ${error.message}`);
      if (routeLayer && map.hasLayer(routeLayer)) {
        map.removeLayer(routeLayer);
        routeLayer = null;
      }
    }
  } finally {
    activeController = null;
    console.log("Global activeController reset in apiRespond finally.");
  }
}

function drawRouteOnMap(coordinates) {
  if (!map) {
    console.warn("Map not available for drawing route.");
    return;
  }

  if (routeLayer) {
    map.removeLayer(routeLayer);
    routeLayer = null;
    console.log("Previous route layer removed.");
  }

  const latLngs = coordinates
    .map((coord) => {
      if (
        Array.isArray(coord) &&
        coord.length >= 2 &&
        typeof coord[0] === "number" &&
        typeof coord[1] === "number"
      ) {
        return [coord[1], coord[0]];
      } else {
        console.warn("Invalid coordinate format found:", coord);
        return null;
      }
    })
    .filter((coord) => coord !== null);

  if (latLngs.length === 0) {
    console.warn("No valid coordinates to draw route.");
    return;
  }

  routeLayer = L.polyline(latLngs, { color: "blue", weight: 5, opacity: 0.7 });
  routeLayer.addTo(map);
  console.log(`Route drawn with ${latLngs.length} points.`);

  map.fitBounds(routeLayer.getBounds().pad(0.1));
}
