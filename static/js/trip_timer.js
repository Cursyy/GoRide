let socket;
let timerInterval = null;
let baseTime = 0;
let startedAt = null;
let isLocalTimerRunning = false;
let baseTimerDisplayElement;
let globalTripStatusContainer;
let tripTimerElement;
let tripButtonsContainer;

function formatDuration(totalSeconds) {
  if (isNaN(totalSeconds) || totalSeconds < 0) {
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

function updateTimerDisplay(text) {
  if (baseTimerDisplayElement) {
    baseTimerDisplayElement.textContent = text;
  }
  if (tripTimerElement) {
    tripTimerElement.textContent = text;
  }
}

function showGlobalTripStatus(show = true) {
  if (globalTripStatusContainer) {
    globalTripStatusContainer.style.display = show ? "block" : "none";
  }
}

function startLocalTimer(initialServerTime = null) {
  if (timerInterval) clearInterval(timerInterval);

  console.log(
    `Attempting to start local timer. baseTime: ${baseTime}s, startedAt: ${
      startedAt ? new Date(startedAt).toISOString() : "null"
    }`,
  );

  if (startedAt === null || typeof startedAt === "undefined") {
    console.error("startLocalTimer cannot proceed: startedAt is not set.");
    updateTimerDisplay("Error: Sync failed.");
    isLocalTimerRunning = false;
    return;
  }

  let displayTime;
  if (initialServerTime !== null && !isNaN(initialServerTime)) {
    displayTime = initialServerTime;
    console.log(`Initial display using server_time: ${displayTime}s`);
  } else {
    displayTime = baseTime + Math.floor((Date.now() - startedAt) / 1000);
    console.log(`Initial display calculated locally: ${displayTime}s`);
  }
  updateTimerDisplay(`${formatDuration(displayTime)} Trip in progress...`);
  showGlobalTripStatus(true);

  timerInterval = setInterval(() => {
    const now = Date.now();
    if (startedAt === null) {
      console.error("startedAt became null inside interval! Stopping timer.");
      stopLocalTimer("Error: Sync lost.");
      return;
    }
    const elapsedSinceStart = Math.floor((now - startedAt) / 1000);
    const totalElapsed = baseTime + elapsedSinceStart;
    updateTimerDisplay(`${formatDuration(totalElapsed)} Trip in progress...`);
  }, 1000);
  isLocalTimerRunning = true;
  console.log("Shared local timer started.");
}

function stopLocalTimer(displayText = "") {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = null;
  isLocalTimerRunning = false;
  updateTimerDisplay(displayText);
  console.log("Shared local timer stopped. Display:", displayText);

  if (
    !displayText ||
    displayText.includes("finished") ||
    displayText.includes("not started") ||
    displayText.includes("No current trip") ||
    displayText.includes("Error") ||
    displayText.includes("closed")
  ) {
    showGlobalTripStatus(false);
  } else {
    showGlobalTripStatus(true);
  }
}

function initializeWebSocket() {
  socket = new WebSocket(`ws://${window.location.host}/ws/trip/status/`);

  socket.onopen = function () {
    console.log("WebSocket connection opened (shared).");
    console.log("Requesting initial status (shared).");
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "get_status" }));
    } else {
      console.error("Socket closed before sending get_status in onopen");
    }
    updateTimerDisplay("Checking trip status...");
  };

  socket.onmessage = function (event) {
    if (!baseTimerDisplayElement) {
      console.error(
        "Critical: baseTimerDisplayElement not found in onmessage. Aborting.",
      );
      baseTimerDisplayElement = document.getElementById("base-timer-display");
      if (!baseTimerDisplayElement) return;
    }

    console.log("WebSocket message received (shared):", event.data);
    let data;
    try {
      data = JSON.parse(event.data);
    } catch (e) {
      return;
    }

    if (data.error) {
      return;
    }

    const currentStatus = data.status;
    const serverTotalTime = data.total_travel_time || 0;
    const serverCurrentTime = data.server_time || 0;

    console.log(
      `Processing status (shared): '${currentStatus}', isLocalTimerRunning: ${isLocalTimerRunning}, serverTotalTime: ${serverTotalTime}, serverCurrentTime: ${serverCurrentTime}`,
    );

    let timerText = "";

    if (currentStatus === "finished") {
      timerText = `Trip finished. Duration: ${formatDuration(
        serverTotalTime,
      )}.`;
      baseTime = 0;
      startedAt = null;
      if (isLocalTimerRunning) stopLocalTimer(timerText);
      else updateTimerDisplay(timerText);
      showGlobalTripStatus(false);
    } else if (currentStatus === "active" || currentStatus === "resumed") {
      baseTime = serverTotalTime;

      if (!isLocalTimerRunning) {
        console.log(">>> Shared: Starting timer based on received status.");
        startedAt = Date.now();
        startLocalTimer(serverCurrentTime);
      } else {
        console.log(">>> Shared: Timer already running, baseTime updated.");
        if (startedAt) {
          const localElapsedSinceStart = Math.floor(
            (Date.now() - startedAt) / 1000,
          );
          const localTotalElapsed = baseTime + localElapsedSinceStart;
          const drift = Math.abs(localTotalElapsed - serverCurrentTime);

          if (drift > 3) {
            console.warn(
              `Shared: Correcting time drift of ${drift.toFixed(
                1,
              )}s. Local: ${localTotalElapsed}, Server: ${serverCurrentTime}`,
            );
            startedAt =
              Date.now() - Math.max(0, serverCurrentTime - baseTime) * 1000;
            console.log(
              `Drift correction applied. New baseTime: ${baseTime}s, recalculated startedAt: ${new Date(
                startedAt,
              ).toISOString()}`,
            );
            updateTimerDisplay(
              `${formatDuration(serverCurrentTime)} Trip in progress...`,
            );
          }
        } else {
          console.warn(
            "Timer running but startedAt is null. Attempting restart.",
          );
          startedAt =
            Date.now() - Math.max(0, serverCurrentTime - baseTime) * 1000;
          startLocalTimer(serverCurrentTime);
        }
      }
      showGlobalTripStatus(true);
    } else if (currentStatus === "paused") {
      baseTime = serverTotalTime;
      timerText = `${formatDuration(baseTime)} (Paused)`;
      startedAt = null;
      if (isLocalTimerRunning) {
        stopLocalTimer(timerText);
      } else {
        updateTimerDisplay(timerText);
      }
      showGlobalTripStatus(true);
    } else {
      timerText =
        currentStatus === "none" ? "No current trip" : "Trip not started";
      if (currentStatus !== "not_started" && currentStatus !== "none") {
        console.warn("Received unknown status (shared):", currentStatus);
        timerText = "Unknown status";
      }
      baseTime = 0;
      startedAt = null;
      if (isLocalTimerRunning) stopLocalTimer(timerText);
      else updateTimerDisplay(timerText);
      showGlobalTripStatus(false);
    }

    if (typeof updateTripButtons === "function" && tripButtonsContainer) {
      updateTripButtons(currentStatus);
    }
  };

  socket.onerror = function (error) {
    console.error("WebSocket Error (shared):", error);
    baseTime = 0;
    startedAt = null;
    stopLocalTimer("Connection error.");
    if (typeof updateTripButtons === "function")
      updateTripButtons("not_started");
  };

  socket.onclose = function (event) {
    console.log(
      "WebSocket connection closed (shared):",
      event.reason,
      `(Code: ${event.code})`,
    );
    baseTime = 0;
    startedAt = null;
    stopLocalTimer("Connection closed.");
    if (typeof updateTripButtons === "function")
      updateTripButtons("not_started");
  };
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM fully loaded (shared script).");

  baseTimerDisplayElement = document.getElementById("base-timer-display");
  globalTripStatusContainer = document.getElementById("global-trip-status");
  tripTimerElement = document.getElementById("trip-timer");
  tripButtonsContainer = document.getElementById("trip-buttons");

  if (!baseTimerDisplayElement)
    console.error(
      "Shared Init Error: Element '#base-timer-display' not found!",
    );
  if (!globalTripStatusContainer)
    console.error(
      "Shared Init Error: Element '#global-trip-status' not found!",
    );
  if (!tripTimerElement)
    console.log(
      "Shared Init Info: Element '#trip-timer' not found (expected on non-control pages).",
    );
  if (!tripButtonsContainer)
    console.log(
      "Shared Init Info: Element '#trip-buttons' not found (expected on non-control pages).",
    );

  initializeWebSocket();

  showGlobalTripStatus(false);
  updateTimerDisplay("Connecting...");
});
