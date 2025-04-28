document.addEventListener("DOMContentLoaded", () => {
  const filterForm = document.getElementById("event-filter-form");
  const eventsContainer = document.getElementById("events-container");
  const loadingIndicator = document.getElementById("loading-indicator");
  const noResultsMessage = document.getElementById("no-results");
  const radiusSlider = document.getElementById("radius-filter");
  const radiusDisplay = document.getElementById("radius-display");
  const latInput = document.getElementById("lat-filter");
  const lonInput = document.getElementById("lon-filter");
  const locationInput = document.getElementById("location-filter");
  const useMyLocationBtn = document.getElementById("use-my-location-btn");
  const resetFiltersBtn = document.getElementById("reset-filters-btn");

  if (radiusSlider && radiusDisplay) {
    radiusSlider.addEventListener("input", () => {
      radiusDisplay.textContent = `${radiusSlider.value} km`;
    });
    radiusDisplay.textContent = `${radiusSlider.value} km`;
  }

  const fetchAndDisplayEvents = async (params = {}) => {
    loadingIndicator.style.display = "block";
    eventsContainer.innerHTML = "";
    noResultsMessage.style.display = "none";

    let apiUrl;
    const queryParams = new URLSearchParams();

    if (params.lat && params.lon) {
      apiUrl = "api/search/nearby/";
      console.log("Using NEARBY API endpoint");
      for (const key in params) {
        if (params[key]) {
          queryParams.append(key, params[key]);
        }
      }
    } else {
      apiUrl = "api/search/default/";
      console.log("Using DEFAULT API endpoint");
      for (const key in params) {
        if (
          key !== "lat" &&
          key !== "lon" &&
          key !== "radius" &&
          key !== "unit" &&
          params[key]
        ) {
          queryParams.append(key, params[key]);
        }
      }
    }

    const queryString = queryParams.toString();
    const fullUrl = queryString ? `${apiUrl}?${queryString}` : apiUrl;
    console.log("Fetching events from:", fullUrl);

    try {
      const response = await fetch(fullUrl);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("API Error Response:", errorData);
        throw new Error(
          `HTTP error! status: ${response.status} - ${
            errorData.error || response.statusText
          }`,
        );
      }
      const data = await response.json();
      console.log("Received data:", data);
      displayEvents(data.events || []);
    } catch (error) {
      console.error("Error fetching events:", error);
      eventsContainer.innerHTML = `<p class="error-message">Could not load events: ${error.message}. Please try again later.</p>`;
    } finally {
      loadingIndicator.style.display = "none";
    }
  };

  const displayEvents = (events) => {
    if (!events || events.length === 0) {
      noResultsMessage.style.display = "block";
      return;
    }

    events.forEach((event) => {
      const imageUrl = event.images?.[0]?.url;
      const eventName = event.name || "Unnamed Event";
      const eventUrl = event.url || "#";
      const startDate = event.dates?.start?.localDate;
      const startTime = event.dates?.start?.localTime;
      const venueData = event._embedded?.venues?.[0];
      const venueName = venueData?.name || "";
      const cityName = venueData?.city?.name || "";
      const countryName = venueData?.country?.name || "";
      const genre = event.classifications?.[0]?.genre?.name || "";
      const longitude = venueData?.location?.longitude || "";
      const latitude = venueData?.location?.latitude || "";

      let displayDate = "Date N/A";
      if (startDate) {
        try {
          const dateOpts = { year: "numeric", month: "long", day: "numeric" };
          displayDate = new Date(startDate).toLocaleDateString(
            undefined,
            dateOpts,
          );
          if (startTime) {
            const timeOpts = {
              hour: "2-digit",
              minute: "2-digit",
              hour12: false,
            };
            const timeStr =
              startTime.length === 5 ? startTime + ":00" : startTime;
            displayDate += ` - ${new Date(
              `${startDate}T${timeStr}`,
            ).toLocaleTimeString(undefined, timeOpts)}`;
          }
        } catch (e) {
          console.error("Date formatting error", e);
        }
      }

      let displayVenue = [venueName, cityName, countryName]
        .filter(Boolean)
        .join(", ");
      if (!displayVenue) displayVenue = "Venue N/A";

      const card = document.createElement("article");
      card.className = "event-card";
      card.innerHTML = `
                <img src="${imageUrl}" alt="${eventName}" class="event-card__image" loading="lazy">
                <div class="event-card__content">
                    <h3 class="event-card__title">${eventName}</h3>
                    <p class="event-card__info">
                        <i class="fas fa-calendar-alt"></i> ${displayDate}
                    </p>
                    <p class="event-card__info">
                         <i class="fas fa-map-marker-alt"></i>
                        ${displayVenue}
                    </p>
                    ${
                      genre
                        ? `<p class="event-card__info"><i class="fas fa-tag"></i> ${genre}</p>`
                        : ""
                    }

                    <div class="event-card__footer">
                        <a href="${eventUrl}" target="_blank" rel="noopener noreferrer" class="event-card__link">
                            View Event  <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                    <div class="event-card__directions">
                        
                </div>
            `;
      const directionsContainer = card.querySelector(".event-card__directions");

      if (latitude && longitude && directionsContainer) {
        const directionsButton = document.createElement("button");
        directionsButton.className = "event-card__directions-button";
        directionsButton.innerHTML = `<i class="fas fa-directions"></i> Get Directions`;

        directionsButton.addEventListener("click", () => {
          const mapPageUrl = "/en/get_direction/";

          const urlWithParams = `${mapPageUrl}?lat=${latitude}&lon=${longitude}`;

          window.location.href = urlWithParams;
        });

        directionsContainer.appendChild(directionsButton);
      } else if (directionsContainer) {
        directionsContainer.innerHTML = `<p class="event-card__info--small">Directions unavailable</p>`;
      }

      eventsContainer.appendChild(card);
    });
  };

  filterForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const formData = new FormData(filterForm);
    const params = {};
    for (const [key, value] of formData.entries()) {
      if (value) {
        params[key] = value;
      }
      console.log(`Filter param: ${key} = ${value}`);
    }
    if (!latInput.value || !lonInput.value) {
      delete params.lat;
      delete params.lon;
      delete params.radius;
    }

    fetchAndDisplayEvents(params);
  });

  useMyLocationBtn.addEventListener("click", () => {
    if (navigator.geolocation) {
      useMyLocationBtn.disabled = true;
      useMyLocationBtn.textContent = `Getting location...`;
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;
          latInput.value = lat.toFixed(6);
          lonInput.value = lon.toFixed(6);
          locationInput.value = "My Location";
          console.log(`Location acquired: ${lat}, ${lon}`);
          useMyLocationBtn.disabled = false;
          useMyLocationBtn.textContent = "Use My Location";
        },
        (error) => {
          console.error("Error getting geolocation:", error);
          alert(
            `Could not get your location. Please ensure location services are enabled and permissions are granted.`,
          );
          useMyLocationBtn.disabled = false;
          useMyLocationBtn.textContent = `Use My Location`;
        },
        { enableHighAccuracy: false, timeout: 10000, maximumAge: 0 },
      );
    } else {
      alert(`Geolocation is not supported by your browser.`);
    }
  });

  resetFiltersBtn.addEventListener("click", () => {
    filterForm.reset();
    latInput.value = "";
    lonInput.value = "";
    if (radiusSlider && radiusDisplay) {
      radiusDisplay.textContent = `${radiusSlider.value} km`;
    }
    fetchAndDisplayEvents();
  });

  fetchAndDisplayEvents(initialParams);

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        initialParams.lat = position.coords.latitude.toFixed(6);
        initialParams.lon = position.coords.longitude.toFixed(6);
        initialParams.radius = radiusSlider ? radiusSlider.value : "15";
        console.log("Initial load with user location.");
        fetchAndDisplayEvents(initialParams);
      },
      (error) => {
        console.warn(
          "Could not get initial location, loading default events.",
          error.message,
        );
        fetchAndDisplayEvents();
      },
      { timeout: 5000 },
    );
  } else {
    console.log("Geolocation not supported, loading default events.");
    fetchAndDisplayEvents();
  }
});
