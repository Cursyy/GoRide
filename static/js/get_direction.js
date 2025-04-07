let map;
let userLat, userLon;
let markers = [];
let waypoints = [];
let route;
let turnByTurnLayer;
let userMarkersCount;
let timerInterval = null;
let startedAt = null;
let baseTime = 0;
let isLocalTimerRunning = false;
let syncInterval = null;

const categoriesList =
  "accommodation,activity,airport,commercial,catering,education,entertainment,healthcare,leisure,natural,national_park,railway,service,tourism,religion,amenity,beach,public_transport";
const socket = new WebSocket(`ws://${window.location.host}/ws/trip/status/`);

const categories = categoriesList.split(",");

const groupedCategories = {};
const simpleCategories = [];

categories.forEach((cat) => {
  if (cat.indexOf(".") === -1) {
    simpleCategories.push(cat);
  } else {
    const parts = cat.split(".");
    const parent = parts[0];
    if (!groupedCategories[parent]) {
      groupedCategories[parent] = [];
    }
    groupedCategories[parent].push(cat);
  }
});
function renderResults(results) {
  const resultsContainer = document.getElementById("places-container");
  resultsContainer.innerHTML = "";

  results.forEach((result) => {
    let resultHTML = `
            <div class="result-item">
                    <div class="result-content">
                        <h5 class="result-title">${
                          result.name || "No name available"
                        }</h5>
                        <p><strong>Address:</strong> ${
                          result.address_line2 || ""
                        }</p>
                        <p><strong>Distance:</strong> ${
                          result.distance
                        } meters</p>
                        <p><strong>Estimated Time:</strong> ${Math.ceil(
                          result.distance / 5.5 / 60,
                        )} minutes</p>
                    </div>
                </div>
        `;
    resultsContainer.innerHTML += resultHTML;
  });
}

function renderCategories() {
  const categoriesContainer = document.getElementById("categories-container");
  let html = "";

  simpleCategories.forEach((cat) => {
    html += `
            <li>
                <a class="dropdown-item" href="#" onclick="searchPlaces('${cat}'); return false;">${cat}</a>
            </li>`;
  });

  categoriesContainer.innerHTML = html;
}
function startLocalTimer() {
  if (!tripTimer) {
    console.error("startLocalTimer: tripTimer element not found!");
    isLocalTimerRunning = false;
    return;
  }
  if (timerInterval) clearInterval(timerInterval);

  console.log(
    `Attempting to start local timer. baseTime: ${baseTime}s, startedAt: ${
      startedAt ? new Date(startedAt).toISOString() : "null"
    }`,
  );

  if (startedAt === null || typeof startedAt === "undefined") {
    console.error(
      "startLocalTimer cannot proceed: startedAt is not set. Stopping.",
    );
    if (tripTimer) tripTimer.textContent = "Error: Timer sync failed.";
    isLocalTimerRunning = false;
    return;
  }

  timerInterval = setInterval(() => {
    const now = Date.now();
    const elapsedSinceStart = Math.floor((now - startedAt) / 1000);
    const totalElapsed = baseTime + elapsedSinceStart;

    if (tripTimer) {
      tripTimer.textContent = `${formatDuration(
        totalElapsed,
      )} Trip in progress...`;
    } else {
      console.error("tripTimer element lost inside interval!");
      clearInterval(timerInterval);
      isLocalTimerRunning = false;
    }
  }, 1000);
  isLocalTimerRunning = true;
  console.log("Local timer started successfully.");
}

function updateTripButtons(status) {
  console.log("Updating trip buttons with status:", status);
  if (!tripButtons) {
    console.error("updateTripButtons: tripButtons element not found!");
    return;
  }
  tripButtons.innerHTML = "";

  if (status === "not_started" || status === "none") {
    tripButtons.innerHTML = `<button onclick="startTrip()">Start</button>`;
  } else if (status === "active") {
    tripButtons.innerHTML = `
            <button onclick="pauseTrip()">Pause</button>
            <button onclick="endTrip()">Finish</button>
        `;
  } else if (status === "paused") {
    tripButtons.innerHTML = `
            <button onclick="resumeTrip()">Resume</button>
            <button onclick="endTrip()">Finish</button>
        `;
  } else if (status === "finished") {
    tripButtons.innerHTML = "Trip finished. Thank you!";
  } else if (status === "loading") {
    tripButtons.innerHTML = "Loading status...";
  }
}
function stopLocalTimer(displayText = "") {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = null;
  isLocalTimerRunning = false;
  if (tripTimer && displayText) {
    tripTimer.textContent = displayText;
  } else if (!tripTimer) {
    console.error("stopLocalTimer: tripTimer element not found!");
  }
  console.log("Local timer stopped. Display:", displayText);
}

function syncWithServer(data) {
  const localElapsed = Math.floor((Date.now() - startedAt) / 1000) + baseTime;
  const serverElapsed = Math.floor(data.server_time);

  const drift = Math.abs(localElapsed - serverElapsed);
  if (drift > 2) {
    console.log(`Correcting drift of ${drift}s`);
    baseTime = serverElapsed;
    startedAt = Date.now();
  }
}
function getCookie(name) {
  console.log("Getting cookie:", name);
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
  console.log("Cookie value:", cookieValue);
  return cookieValue;
}

function startTrip() {
  console.log("Starting trip (requesting)...");

  fetch("/get_direction/api/start_trip/", {
    /* ... */
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("Start trip response:", data);
      if (data.error) {
        alert("Start error: " + data.error);

        updateTripButtons("not_started");
      } else {
        console.log(
          "Trip start requested successfully. Waiting for WebSocket update.",
        );
      }
    })
    .catch((error) => {
      console.error("Fetch startTrip error:", error);
      alert("Network error starting trip.");
      updateTripButtons("not_started");
    });
}

function pauseTrip() {
  console.log("Pausing trip (requesting)...");

  fetch("/get_direction/api/pause_trip/", {
    /* ... */
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("Pause trip response:", data);
      if (data.error) {
        alert("Pause error: " + data.error);
      } else {
        console.log(
          "Trip pause requested successfully. Waiting for WebSocket update.",
        );
      }
    })
    .catch((error) => {
      console.error("Fetch pauseTrip error:", error);
      alert("Network error pausing trip.");
    });
}

function resumeTrip() {
  console.log("Resuming trip (requesting)...");

  fetch("/get_direction/api/resume_trip/", {
    /* ... */
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("Resume trip response:", data);
      if (data.error) {
        alert("Resume error: " + data.error);
      } else {
        console.log(
          "Trip resume requested successfully. Waiting for WebSocket update.",
        );
      }
    })
    .catch((error) => {
      console.error("Fetch resumeTrip error:", error);
      alert("Network error resuming trip.");
    });
}

function endTrip() {
  console.log("Ending trip (requesting)...");
  fetch("/get_direction/api/end_trip/", {
    /* ... */
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("End trip response:", data);
      if (data.error) {
        alert("End error: " + data.error);
      } else {
        console.log(
          "Trip end requested successfully. Waiting for WebSocket update.",
        );
      }
    })
    .catch((error) => {
      console.error("Fetch endTrip error:", error);
      alert("Network error ending trip.");
    });
}

socket.onopen = function () {
  console.log("WebSocket connection opened.");
  console.log("Requesting initial status via WebSocket.");
  socket.send(JSON.stringify({ type: "get_status" }));
};

socket.onmessage = function (event) {
  if (!tripTimer || !tripButtons) {
    console.warn(
      "socket.onmessage received before DOM elements were ready. This shouldn't normally happen if elements are fetched in DOMContentLoaded.",
    );

    tripTimer = document.getElementById("trip-timer");
    tripButtons = document.getElementById("trip-buttons");
    if (!tripTimer || !tripButtons) {
      console.error(
        "Critical: DOM elements not found even on retry in onmessage. Aborting message processing.",
      );
      return;
    }
  }

  console.log("WebSocket message received:", event.data);
  let data;
  try {
    data = JSON.parse(event.data);
    console.log("Parsed data:", data);
  } catch (e) {
    console.error("Failed to parse WebSocket message:", e);
    return;
  }

  if (data.error) {
    console.error(
      "WebSocket error from server:",
      data.error,
      data.details || "",
    );
    if (tripTimer) tripTimer.textContent = `Error: ${data.error}`;
    updateTripButtons("not_started");
    return;
  }

  const currentStatus = data.status;
  const serverTotalTime = data.total_travel_time || 0;

  console.log(
    `Processing status: '${currentStatus}', Current isLocalTimerRunning state: ${isLocalTimerRunning}`,
  );

  if (currentStatus === "finished") {
    if (
      isLocalTimerRunning ||
      (tripTimer && !tripTimer.textContent.startsWith("Trip finished"))
    ) {
      const finalDuration = formatDuration(serverTotalTime);
      stopLocalTimer(`Trip finished. Duration: ${finalDuration}. Thank you!`);
    }
    updateTripButtons("finished");
  } else if (currentStatus === "active" || currentStatus === "resumed") {
    baseTime = serverTotalTime;

    if (!isLocalTimerRunning) {
      startedAt = Date.now();
      startLocalTimer();
    } else {
      console.log(
        ">>> Condition '!isLocalTimerRunning' is FALSE. Timer already running, updating baseTime.",
      );
      if (startedAt) {
        const localElapsedSinceStart = Math.floor(
          (Date.now() - startedAt) / 1000,
        );
        const localTotalElapsed = baseTime + localElapsedSinceStart;
        const serverCurrentTime = data.server_time || 0;
        const drift = Math.abs(localTotalElapsed - serverCurrentTime);
        if (drift > 3) {
          console.warn(`Correcting time drift of ${drift.toFixed(1)}s.`);
          baseTime = serverTotalTime;
          startedAt = Date.now();
          console.log(
            `Drift correction applied. New baseTime: ${baseTime}s, new startedAt: ${new Date(
              startedAt,
            ).toISOString()}`,
          );
        }
      }
    }
    updateTripButtons("active");
  } else if (currentStatus === "paused") {
    if (isLocalTimerRunning) {
      console.log("Status changed to paused. Stopping local timer.");
      baseTime = serverTotalTime;
      stopLocalTimer(`${formatDuration(serverTotalTime)} (Paused)`);
    } else {
      if (tripTimer)
        tripTimer.textContent = `${formatDuration(serverTotalTime)} (Paused)`;
    }
    updateTripButtons("paused");
  } else if (
    currentStatus === "not_started" ||
    currentStatus === "none" ||
    !currentStatus
  ) {
    if (
      isLocalTimerRunning ||
      (tripTimer &&
        !tripTimer.textContent.includes("not started") &&
        !tripTimer.textContent.includes("No current trip"))
    ) {
      console.log(
        "Status is not_started/none. Stopping local timer and resetting.",
      );
      stopLocalTimer(
        currentStatus === "none" ? "No current trip" : "Trip not started",
      );
    } else if (tripTimer) {
      tripTimer.textContent =
        currentStatus === "none" ? "No current trip" : "Trip not started";
    }
    updateTripButtons("not_started");
    baseTime = 0;
    startedAt = null;
  } else {
    console.warn("Received unknown status:", currentStatus);
    updateTripButtons("not_started");
  }
};

socket.onerror = function (error) {
  console.error("WebSocket Error:", error);
  if (tripTimer) tripTimer.textContent = "Connection error.";
  updateTripButtons("not_started");
};

socket.onclose = function (event) {
  console.log(
    "WebSocket connection closed:",
    event.reason,
    `(Code: ${event.code})`,
  );
  if (tripTimer) tripTimer.textContent = "Connection closed.";
  stopLocalTimer();
  updateTripButtons("not_started");
};

document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM fully loaded and parsed");

  tripTimer = document.getElementById("trip-timer");
  tripButtons = document.getElementById("trip-buttons");

  if (!tripTimer)
    console.error(
      "Initialization Error: Element with ID 'trip-timer' not found!",
    );
  if (!tripButtons)
    console.error(
      "Initialization Error: Element with ID 'trip-buttons' not found!",
    );

  if (tripTimer) tripTimer.textContent = "Connecting...";
  updateTripButtons("loading");

  if (!socket) {
    console.error(
      "WebSocket object ('socket') was not initialized before DOMContentLoaded!",
    );
    if (tripTimer) tripTimer.textContent = "Initialization Error.";
    updateTripButtons("not_started");
  } else {
    console.log("DOM ready. WebSocket state:", socket.readyState);

    if (socket.readyState === WebSocket.OPEN) {
      console.log(
        "WebSocket was already open on DOMContentLoaded. Requesting status.",
      );
      socket.send(JSON.stringify({ type: "get_status" }));
    }
  }
});
function formatDuration(totalSeconds) {
  if (isNaN(totalSeconds) || totalSeconds < 0) {
    console.warn("formatDuration received invalid input:", totalSeconds);
    totalSeconds = 0;
  }
  const hours = String(Math.floor(totalSeconds / 3600)).padStart(2, "0");
  const minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(
    2,
    "0",
  );
  const seconds = String(Math.floor(totalSeconds % 60)).padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}

async function searchLocations() {
  const searchInput = document.getElementById("search-input").value;
  console.log("Searching for:", searchInput);

  clearMarkers();

  const response = await fetch(`/en/get_direction/api/search/${searchInput}/`);
  const data = await response.json();
  console.log(data);

  const results = data.results.map((result) => ({
    name: result.name,
    address_line1: result.address_line1,
    address_line2: result.address_line2,
    distance: result.distance,
    distance_units: result.properties?.distance_units,
    time: result.properties?.time,
    lat: result.lat,
    lon: result.lon,
  }));

  renderResults(results);

  data.results.forEach((result) => {
    if (result.rank.confidence > 0.5) {
      const lon = result.lon;
      const lat = result.lat;
      const marker = L.marker([lat, lon])
        .addTo(map)
        .bindPopup(result.formatted);
      markers.push(marker);
      marker.on("click", () => {
        waypoints.push([lat, lon]);
        createButton("get-direction-button", "Get Direction");
      });
    }
  });
}

async function searchPlaces(value) {
  clearMarkers();

  const response = await fetch(
    `/en/get_direction/api/places/${value}/${userLat}/${userLon}`,
  );
  const data = await response.json();
  console.log(data);
  const results = data.features.map((result) => ({
    name: result.properties?.name,
    address_line1: result.properties?.address_line1,
    address_line2: result.properties?.address_line2,
    distance: result.properties?.distance,
    distance_units: result.properties?.distance_units,
    time: result.properties?.time ? result.properties.time : null,
    lat: result.lat,
    lon: result.lon,
  }));

  renderResults(results);
  data.features.forEach((place) => {
    const [lon, lat] = place.geometry.coordinates;
    const marker = L.marker([lat, lon]).addTo(map).bindPopup(`
            ${place.properties.address_line1}<br>
            ${place.properties.address_line2}
        `);
    markers.push(marker);
    marker.on("click", () => {
      waypoints.push([lat, lon]);
      createButton("get-direction-button", "Get Direction");
    });
  });
}

if (!document.getElementById("results-container")) {
  const resultsContainer = document.createElement("div");
  resultsContainer.id = "results-container";
  document.body.appendChild(resultsContainer);
}

async function getRoute(waypoints) {
  clearRoute();
  waypoints.push([userLat, userLon]);
  try {
    console.log("Send waypoints:", waypoints);

    const response = await fetch(`/en/get_direction/api/route/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ waypoints: waypoints }),
    });

    if (!response.ok) throw new Error("Failed to fetch route");

    const result = await response.json();
    route = L.geoJSON(result, {
      style: (feature) => ({
        color: "rgba(20, 137, 255, 0.7)",
        weight: 5,
      }),
    })
      .bindPopup((layer) => {
        return `${layer.feature.properties.distance} ${layer.feature.properties.distance_units}, ${layer.feature.properties.time}`;
      })
      .addTo(map);

    turnByTurns = [];

    result.features.forEach((feature) => {
      feature.properties.legs.forEach((leg, legIndex) => {
        leg.steps.forEach((step) => {
          if (step.instruction && step.instruction.text) {
            turnByTurns.push({
              type: "Feature",
              geometry: {
                type: "Point",
                coordinates:
                  feature.geometry.coordinates[legIndex][step.from_index],
              },
              properties: {
                instruction: step.instruction.text,
              },
            });
          }
        });
      });
    });

    if (turnByTurns.length > 0) {
      turnByTurnLayer = L.geoJSON(
        {
          type: "FeatureCollection",
          features: turnByTurns,
        },
        {
          pointToLayer: (feature, latlng) => {
            return L.circleMarker(latlng, {
              radius: 5,
              color: "#FF5733",
            });
          },
        },
      )
        .bindPopup((layer) => `${layer.feature.properties.instruction}`)
        .addTo(map);
    } else {
      console.warn("There are no available turns to show.");
    }
  } catch (err) {
    console.error("Error fetching route:", err);
  }
}

function clearRoute() {
  if (route) {
    map.removeLayer(route);
    route = null;
  }

  if (turnByTurnLayer) {
    map.removeLayer(turnByTurnLayer);
    turnByTurnLayer = null;
  }

  waypoints = [];
  createButton("get-direction", "Get Direction");
}
function clearMarkers() {
  markers.forEach((marker) => map.removeLayer(marker));
  markers = [];
}

let html = "";

simpleCategories.forEach((cat) => {
  html += `<button class="category-btn" onclick="searchPlaces('${cat}')">${cat}</button>`;
});

for (const parent in groupedCategories) {
  const subcats = groupedCategories[parent];

  if (subcats.length > 1) {
    html += `
            <div class="dropdown" style="display:inline-block;">
                <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdown-${parent}" data-bs-toggle="dropdown" aria-expanded="false">
                    ${parent}
                </button>
                <ul class="dropdown-menu" aria-labelledby="dropdown-${parent}">`;
    subcats.forEach((subcat) => {
      html += `<li><a class="dropdown-item" href="#" onclick="searchPlaces('${subcat}'); return false;">${subcat}</a></li>`;
    });
    html += `</ul>
            </div>`;
  } else {
    html += `<button class="category-btn" onclick="searchPlaces('${subcats[0]}')">${subcats[0]}</button>`;
  }
}

document.getElementById("categories-container").innerHTML = html;

if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(showPosition, showError);
} else {
  console.log("Geolocation is not supported by this browser.");
}

function initializeMap() {
  map = L.map("map").setView([53.347854, -6.259504], 13);
  L.tileLayer(
    "https://maps.geoapify.com/v1/tile/klokantech-basic/{z}/{x}/{y}.png?apiKey=d16fda76e6fc4822bbc407474c620a8e",
    {
      attribution:
        'Powered by <a href="https://www.geoapify.com/" target="_blank">Geoapify</a>',
      maxZoom: 20,
    },
  ).addTo(map);
}
initializeMap();

function showPosition(position) {
  let button = document.getElementById("userLocation");
  button.addEventListener("click", function () {
    userLat = position.coords.latitude;
    userLon = position.coords.longitude;
    if (map) {
      map.setView([userLat, userLon], 15);
    }
  });
  if (window.userMarker) {
    window.userMarker.setLatLng([userLat, userLon]);
  } else {
    let userIcon = L.icon({
      iconUrl: "/static/images/you_are_here.png",
      iconSize: [38, 50],
      iconAnchor: [22, 38],
      popupAnchor: [-3, -38],
    });
    window.userMarker = L.marker([userLat, userLon], { icon: userIcon })
      .bindPopup("You are here")
      .openPopup()
      .addTo(map);
  }
}

function showError(error) {
  console.error("Error getting location:", error.message);
}

if (navigator.geolocation) {
  navigator.geolocation.watchPosition(showPosition, showError, {
    enableHighAccuracy: true,
    maximumAge: 0,
  });
} else {
  console.log("Geolocation is not supported by this browser.");
}

function createButton(buttonId, buttonText) {
  let button = document.getElementById(buttonId);

  if (!button) {
    button = document.createElement("button");
    button.id = buttonId;
    button.textContent = buttonText;
    button.classList.add("map-button");
  }

  button.onclick = null;

  button.addEventListener("click", function () {
    if (buttonId === "get-direction") {
      getRoute(waypoints);
    } else if (buttonId === "delete-markers-button") {
      clearMarkers();
      clearRoute();
    } else if (buttonId === "add-stops-button") {
      map.on("dblclick", async (e) => {
        const { lat, lng } = e.latlng;
        try {
          const response = await fetch(
            `/en/get_direction/api/get_address_marker/${lat}/${lng}`,
          );
          if (!response.ok) throw new Error("Can't find address.");
          const data = await response.text();
          const marker = L.marker([lat, lng])
            .addTo(map)
            .bindPopup(data)
            .openPopup();
          markers.push(marker);
          waypoints.push([lat, lng]);

          if (waypoints.length > 1) {
            getRoute(waypoints);
          }
          createButton("add-stops-button", "Add more stops");
          createButton("delete-markers-button", "Delete my markers");
        } catch (error) {
          console.error("Error:", error);
        }
      });
    }
  });

  return button;
}

function addMapControls() {
  const controlDiv = L.control({ position: "topleft" });

  controlDiv.onAdd = function () {
    const container = L.DomUtil.create("div", "map-buttons-container");
    container.appendChild(createButton("get-direction", "Get Directions"));
    container.appendChild(createButton("add-stops-button", "Add more stops"));
    container.appendChild(
      createButton("delete-markers-button", "Delete my markers"),
    );
    return container;
  };

  controlDiv.addTo(map);
}

map.on("dblclick", async (e) => {
  const { lat, lng } = e.latlng;
  try {
    const response = await fetch(
      `/en/get_direction/api/get_address_marker/${lat}/${lng}`,
    );
    if (!response.ok) throw new Error("Can't find address.");
    const data = await response.text();

    const marker = L.marker([lat, lng]).addTo(map).bindPopup(data).openPopup();
    markers.push(marker);
    waypoints.push([lat, lng]);

    if (waypoints.length > 1) {
      getRoute(waypoints);
    }
  } catch (error) {
    console.error("Error:", error);
  }
});

addMapControls();

document.addEventListener("DOMContentLoaded", renderCategories);
