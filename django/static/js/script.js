document.addEventListener("DOMContentLoaded", function () {
  const progressBar = document.querySelector(".progress-bar");
  if (progressBar) {
    let progress = parseFloat(progressBar.dataset.progress);
    if (progress < 10) {
      progressBar.style.backgroundColor = "#dc3545";
    } else if (progress < 30) {
      progressBar.style.backgroundColor = "#fd7e14";
    } else {
      progressBar.style.backgroundColor = "#28a745";
    }
  }
  if (!window.GLOBAL_USER_LOCATION_AVAILABLE) {
    askForLocationAndSave();
  }
});

function askForLocationAndSave() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        window.GLOBAL_USER_LATITUDE = latitude;
        window.GLOBAL_USER_LONGITUDE = longitude;
        window.GLOBAL_USER_LOCATION_AVAILABLE = true;

        sendLocationToServer(latitude, longitude);
      },
      function (error) {
        console.error("Geolocation Error:", error.message);
      },
      { timeout: 10000, maximumAge: 60000, enableHighAccuracy: false },
    );
  } else {
    console.log("Geolocation is not supported by this browser.");
  }
}

function sendLocationToServer(latitude, longitude) {
  const SAVE_LOCATION_URL = "api/save_location/";

  fetch(SAVE_LOCATION_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({
      latitude: latitude,
      longitude: longitude,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        console.error("Server error saving location:", response.statusText);
      }
      return response.json();
    })
    .then((data) => {
      if (data.status === "success") {
      } else {
        console.error(
          "Failed to save location:",
          data.message || "Unknown error",
        );
      }
    })
    .catch((error) => console.error("Network error sending location:", error));
}

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
