document.addEventListener("DOMContentLoaded", () => {
  const filterForm = document.getElementById("event-filter-form");
  const eventsContainer = document.getElementById("events-container");
  const loadingIndicator = document.getElementById("loading-indicator");
  const noResultsMessage = document.getElementById("no-results");
  const radiusSlider = document.getElementById("radius-filter");
  const radiusDisplay = document.getElementById("radius-display");
  const latInput = document.getElementById("lat-filter");
  const lonInput = document.getElementById("lon-filter");
  const locationInput = document.getElementById("location-filter"); // Поле для введення локації (не використовується для API напряму)
  const useMyLocationBtn = document.getElementById("use-my-location-btn");
  const resetFiltersBtn = document.getElementById("reset-filters-btn");

  // --- Оновлення відображення радіусу ---
  if (radiusSlider && radiusDisplay) {
    radiusSlider.addEventListener("input", () => {
      radiusDisplay.textContent = `${radiusSlider.value} km`;
    });
    // Ініціалізація початкового значення
    radiusDisplay.textContent = `${radiusSlider.value} km`;
  }

  // --- Функція для отримання та відображення подій ---
  const fetchAndDisplayEvents = async (params = {}) => {
    loadingIndicator.style.display = "block";
    eventsContainer.innerHTML = "";
    noResultsMessage.style.display = "none";

    let apiUrl;
    const queryParams = new URLSearchParams();

    // --- ВИЗНАЧЕННЯ API ЕНДПОІНТУ ---
    if (params.lat && params.lon) {
      // Якщо є координати - використовуємо nearby ендпоінт
      apiUrl = "api/search/nearby/";
      console.log("Using NEARBY API endpoint");
      // Додаємо всі параметри
      for (const key in params) {
        if (params[key]) {
          queryParams.append(key, params[key]);
        }
      }
    } else {
      // Якщо координат немає - використовуємо default ендпоінт
      apiUrl = "api/search/default/";
      console.log("Using DEFAULT API endpoint");
      // Додаємо тільки не-локаційні параметри
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

    // --- ВИПРАВЛЕННЯ: Формуємо ПОВНИЙ URL з параметрами ---
    const queryString = queryParams.toString(); // Перетворюємо параметри в рядок "key=value&key2=value2"
    // Додаємо рядок параметрів до базового URL, тільки якщо він не порожній
    const fullUrl = queryString ? `${apiUrl}?${queryString}` : apiUrl;
    // --- КІНЕЦЬ ВИПРАВЛЕННЯ ---
    console.log("Fetching events from:", fullUrl);

    try {
      const response = await fetch(fullUrl);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({})); // Спробувати отримати тіло помилки
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

  // --- Функція для відображення карток подій ---
  const displayEvents = (events) => {
    if (!events || events.length === 0) {
      noResultsMessage.style.display = "block";
      return;
    }

    events.forEach((event) => {
      // Безпечне отримання даних (з перевірками)
      const imageUrl =
        event.images?.[0]?.url || "/static/images/placeholder.jpg"; // Шлях до заглушки
      const eventName = event.name || "Unnamed Event";
      const eventUrl = event.url || "#";
      const startDate = event.dates?.start?.localDate;
      const startTime = event.dates?.start?.localTime;
      const venueData = event._embedded?.venues?.[0];
      const venueName = venueData?.name || "";
      const cityName = venueData?.city?.name || "";
      const countryName = venueData?.country?.name || "";
      const genre = event.classifications?.[0]?.genre?.name || "";

      // Форматування дати і часу (можна використати бібліотеку типу date-fns або moment.js)
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
            // Додаємо 'T' для коректного парсингу часу в деяких браузерах
            const timeStr =
              startTime.length === 5 ? startTime + ":00" : startTime; // Додаємо секунди, якщо їх немає
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
                            {% trans "View Event" %} <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                </div>
            `;
      eventsContainer.appendChild(card);
    });
  };

  // --- Обробник відправки форми фільтрів ---
  filterForm.addEventListener("submit", (e) => {
    e.preventDefault(); // Заборонити стандартну відправку
    const formData = new FormData(filterForm);
    const params = {};
    // Перебираємо дані форми і додаємо до об'єкту параметрів
    for (const [key, value] of formData.entries()) {
      if (value) {
        // Додаємо тільки якщо значення не порожнє
        params[key] = value;
      }
      console.log(`Filter param: ${key} = ${value}`);
    }
    // Переконуємось, що lat/lon передаються, тільки якщо вони встановлені
    if (!latInput.value || !lonInput.value) {
      delete params.lat;
      delete params.lon;
      delete params.radius; // Можливо, не варто передавати радіус без координат
    }

    fetchAndDisplayEvents(params);
  });

  // --- Обробник кнопки "Використати мою локацію" ---
  useMyLocationBtn.addEventListener("click", () => {
    if (navigator.geolocation) {
      useMyLocationBtn.disabled = true;
      useMyLocationBtn.textContent = `{% trans "Getting location..." %}`;
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;
          latInput.value = lat.toFixed(6); // Зберігаємо координати в прихованих полях
          lonInput.value = lon.toFixed(6);
          locationInput.value = `My Location (${lat.toFixed(3)}, ${lon.toFixed(
            3,
          )})`; // Показуємо користувачу
          console.log(`Location acquired: ${lat}, ${lon}`);
          useMyLocationBtn.disabled = false;
          useMyLocationBtn.textContent = `{% trans "Use My Location" %}`;
          // Опціонально: одразу запустити пошук
          // filterForm.dispatchEvent(new Event('submit'));
        },
        (error) => {
          console.error("Error getting geolocation:", error);
          alert(
            `{% trans "Could not get your location. Please ensure location services are enabled and permissions are granted." %}`,
          );
          useMyLocationBtn.disabled = false;
          useMyLocationBtn.textContent = `{% trans "Use My Location" %}`;
        },
        { enableHighAccuracy: false, timeout: 10000, maximumAge: 0 }, // Опції геолокації
      );
    } else {
      alert(`{% trans "Geolocation is not supported by your browser." %}`);
    }
  });

  // --- Обробник кнопки скидання фільтрів ---
  resetFiltersBtn.addEventListener("click", () => {
    filterForm.reset(); // Скидає значення полів форми
    latInput.value = ""; // Очищуємо приховані поля координат
    lonInput.value = "";
    // Оновлюємо відображення радіусу
    if (radiusSlider && radiusDisplay) {
      radiusDisplay.textContent = `${radiusSlider.value} km`;
    }
    // Запускаємо пошук з порожніми фільтрами (покаже дефолтні результати)
    fetchAndDisplayEvents();
  });

  // --- Початкове завантаження подій ---
  // Можна спробувати отримати локацію користувача при завантаженні
  // або просто завантажити дефолтні події (без параметрів lat/lon)
  //const initialParams = {};
  // Тут можна додати логіку для отримання дефолтної локації, якщо потрібно
  fetchAndDisplayEvents(initialParams);

  // Або, якщо хочемо спробувати отримати локацію користувача одразу:
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        initialParams.lat = position.coords.latitude.toFixed(6);
        initialParams.lon = position.coords.longitude.toFixed(6);
        initialParams.radius = radiusSlider ? radiusSlider.value : "15"; // Використовуємо поточний радіус
        console.log("Initial load with user location.");
        fetchAndDisplayEvents(initialParams);
      },
      (error) => {
        console.warn(
          "Could not get initial location, loading default events.",
          error.message,
        );
        fetchAndDisplayEvents(); // Завантажуємо без локації при помилці
      },
      { timeout: 5000 }, // Короткий таймаут для початкової спроби
    );
  } else {
    console.log("Geolocation not supported, loading default events.");
    fetchAndDisplayEvents(); // Завантажуємо без локації, якщо геолокація не підтримується
  }
});
