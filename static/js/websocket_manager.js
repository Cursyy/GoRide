(function () {
  // IIFE for incapsulation
  "use strict";

  let sharedSocket = null;
  let reconnectTimeout = null;
  const RECONNECT_DELAY = 5000; // Delay before reconnecting (5 sec)
  const messageHandlers = {}; // Object to contain handlers: { 'message_type': [handler1, handler2], ... }
  let isInitialized = false; // flag if manager initialized

  let timerInterval = null;
  let baseTime = 0;
  let startedAt = null;
  let isLocalTimerRunning = false;
  let baseTimerDisplayElement;
  let globalTripStatusContainer;
  let tripTimerElement;
  let tripButtonsContainer;
  let tripSummaryContainer;

  // --- Additional functions ---
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

  function showTripSummary(durationSeconds, totalCost) {
    const formattedDuration = formatDuration(durationSeconds);
    const cost = parseFloat(totalCost);
    const summaryMessage = `Trip finished. Duration: ${formattedDuration}, Total Cost: €${
      isNaN(cost) ? "0.00" : cost.toFixed(2)
    }.`;

    if (tripSummaryContainer) {
      tripSummaryContainer.textContent = summaryMessage;
      tripSummaryContainer.style.display = "block";
    }
    stopLocalTimer("");
    showGlobalTripStatus(false);
  }

  function startLocalTimer(serverCurrentTime) {
    if (timerInterval) clearInterval(timerInterval);
    if (startedAt === null) {
      console.error("startLocalTimer: startedAt is null.");
      updateTimerDisplay("Timer Sync Error");
      isLocalTimerRunning = false;
      return;
    }
    console.log(
      `Starting local timer. baseTime: ${baseTime}, startedAt: ${new Date(
        startedAt,
      ).toISOString()}, serverCurrentTime: ${serverCurrentTime}`,
    );
    isLocalTimerRunning = true;

    updateTimerDisplay(
      `${formatDuration(serverCurrentTime)} Trip in progress...`,
    );
    showGlobalTripStatus(true);

    timerInterval = setInterval(() => {
      const now = Date.now();
      if (startedAt === null) {
        console.error("startedAt became null during interval! Stopping timer.");
        stopLocalTimer("Error: Sync lost.");
        return;
      }
      const elapsedSinceStart = Math.floor((now - startedAt) / 1000);
      const totalElapsed = baseTime + elapsedSinceStart;
      updateTimerDisplay(`${formatDuration(totalElapsed)} Trip in progress...`);
    }, 1000);
    console.log("Local timer running.");
  }

  function stopLocalTimer(displayText = "") {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;
    isLocalTimerRunning = false;
    console.log("Local timer stopped. Display:", displayText);
    updateTimerDisplay(displayText);

    const hideGlobal =
      !displayText ||
      displayText.includes("finished") ||
      displayText.includes("not started") ||
      displayText.includes("No current trip") ||
      displayText.includes("Error") ||
      displayText.includes("closed");

    if (hideGlobal) {
      showGlobalTripStatus(false);
      startedAt = null;
      baseTime = 0;
    } else {
      showGlobalTripStatus(true);
    }
  }

  // ---  WebSocket Manager  ---

  function registerMessageHandler(type, handler) {
    if (typeof handler !== "function") {
      console.error(`Handler for type "${type}" is not a function.`);
      return;
    }
    if (!messageHandlers[type]) {
      messageHandlers[type] = [];
    }
    if (!messageHandlers[type].includes(handler)) {
      messageHandlers[type].push(handler);
      console.log(`Handler registered for message type: ${type}`);
    } else {
      console.warn(`Handler already registered for message type: ${type}`);
    }
  }

  function dispatchMessage(data) {
    if (!data || !data.type) {
      console.error("Received message without type:", data);
      return;
    }

    const handlers = messageHandlers[data.type];
    if (handlers && handlers.length > 0) {
      console.log(
        `Dispatching message type ${data.type} to ${handlers.length} handler(s).`,
      );
      const payload = data.data || data.payload || data;
      handlers.forEach((handler) => {
        try {
          handler(payload);
        } catch (handlerError) {
          console.error(
            `Error in handler for type ${data.type}:`,
            handlerError,
            "Payload:",
            payload,
          );
        }
      });
    } else {
      console.log(`No handler registered for message type: ${data.type}`);
    }

    if (data.type.startsWith("internal_")) {
      const internalHandlers = messageHandlers[data.type];
      if (internalHandlers && internalHandlers.length > 0) {
        console.log(`Dispatching internal event ${data.type}`);
        internalHandlers.forEach((handler) => {
          try {
            handler(data.data || data);
          } catch (e) {
            console.error(e);
          }
        });
      }
    }
  }

  function tryReconnect() {
    if (reconnectTimeout) clearTimeout(reconnectTimeout);
    console.log(`Attempting reconnect in ${RECONNECT_DELAY / 1000} seconds...`);
    reconnectTimeout = setTimeout(() => {
      console.warn("WebSocket attempting to reconnect...");
      initializeSharedWebSocket();
    }, RECONNECT_DELAY);
  }

  function initializeSharedWebSocket() {
    if (!isInitialized) {
      console.log(
        "WebSocket Manager initialization deferred until DOMContentLoaded.",
      );
      return;
    }
    if (sharedSocket && sharedSocket.readyState === WebSocket.CONNECTING) {
      console.log("WebSocket connection attempt already in progress.");
      return;
    }
    if (sharedSocket && sharedSocket.readyState === WebSocket.OPEN) {
      console.log("Shared WebSocket is already open.");
      return;
    }

    console.log("Initializing Shared WebSocket connection...");
    updateTimerDisplay("Connecting...");

    sharedSocket = new WebSocket(
      `ws://${window.location.host}/ws/user/activity/`,
    );

    sharedSocket.onopen = function () {
      console.log("Shared WebSocket connection opened.");
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }
      updateTimerDisplay("Connected");

      dispatchMessage({ type: "internal_socket_open" });

      sendMessage("get_trip_status");
    };

    sharedSocket.onmessage = function (event) {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (e) {
        console.error(
          "Failed to parse WebSocket message:",
          e,
          "Raw Data:",
          event.data,
        );
        return;
      }
      dispatchMessage(data);
    };

    sharedSocket.onerror = function (error) {
      console.error("Shared WebSocket Error:", error);
      dispatchMessage({ type: "internal_socket_error", data: error });
      stopLocalTimer("Connection error.");
    };

    sharedSocket.onclose = function (event) {
      console.log(
        `Shared WebSocket connection closed: Code=${event.code}, Reason=${
          event.reason || "N/A"
        }, Clean=${event.wasClean}`,
      );
      const wasClean = event.wasClean;
      const code = event.code;
      sharedSocket = null;

      dispatchMessage({ type: "internal_socket_close", data: event });

      stopLocalTimer("Connection closed.");

      if (!wasClean && code !== 1000 && code !== 1001 && code !== 4001) {
        tryReconnect();
      } else {
        console.log(
          "WebSocket closed cleanly or due to non-recoverable error. No automatic reconnect.",
        );
      }
    };
  }

  function sendMessage(type, payload = {}) {
    if (!sharedSocket || sharedSocket.readyState !== WebSocket.OPEN) {
      console.error(
        `Cannot send message of type "${type}". WebSocket is not open. State: ${sharedSocket?.readyState}`,
      );
      return false;
    }
    try {
      const message = JSON.stringify({ type, payload });
      sharedSocket.send(message);
      return true;
    } catch (e) {
      console.error(
        `Failed to stringify or send message of type "${type}":`,
        e,
      );
      return false;
    }
  }

  // --- Specific message handlers (internal for manager) ---

  function handleTripStatusUpdate(data) {
    console.log("Manager: Handling trip_status update:", data);
    if (!data) {
      console.warn("handleTripStatusUpdate received invalid data");
      return;
    }

    if (!baseTimerDisplayElement && !tripTimerElement) {
    } else {
      const currentStatus = data.status;
      const serverTotalTime = data.total_travel_time || 0;
      const serverCurrentTime =
        data.server_time !== null ? data.server_time : serverTotalTime;

      let timerText = "";

      if (currentStatus === "finished") {
        const totalCost = data.total_cost ?? 0;
        if (isLocalTimerRunning) stopLocalTimer();
        showTripSummary(serverTotalTime, totalCost);
      } else if (currentStatus === "active" || currentStatus === "resumed") {
        const newBaseTime = serverTotalTime;
        if (!isLocalTimerRunning) {
          baseTime = newBaseTime;
          startedAt = Date.now();
          startLocalTimer(serverCurrentTime);
        } else {
          baseTime = newBaseTime;
          if (startedAt) {
            const localElapsedSinceStart = Math.max(
              0,
              Math.floor((Date.now() - startedAt) / 1000),
            );
            const localTotalElapsed = baseTime + localElapsedSinceStart;
            const drift = Math.abs(localTotalElapsed - serverCurrentTime);

            if (drift > 2) {
              console.warn(
                `Shared: Correcting time drift of ${drift.toFixed(1)}s.`,
              );
              const expectedElapsedSeconds = Math.max(
                0,
                serverCurrentTime - baseTime,
              );
              startedAt = Date.now() - expectedElapsedSeconds * 1000;
              updateTimerDisplay(
                `${formatDuration(serverCurrentTime)} Trip in progress...`,
              );
            } else {
              updateTimerDisplay(
                `${formatDuration(localTotalElapsed)} Trip in progress...`,
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
        if (isLocalTimerRunning) stopLocalTimer(timerText);
        else updateTimerDisplay(timerText);
        startedAt = null;
        showGlobalTripStatus(true);
      } else {
        timerText =
          currentStatus === "none" || currentStatus === null
            ? "No current trip"
            : "Trip not started";
        if (
          currentStatus !== "not_started" &&
          currentStatus !== "none" &&
          currentStatus !== null
        ) {
          console.warn("Received unknown trip status:", currentStatus);
          timerText = "Trip status: Unknown";
        }
        if (isLocalTimerRunning) stopLocalTimer(timerText);
        else updateTimerDisplay(timerText);
        showGlobalTripStatus(false);
      }
    }

    if (
      typeof window.updateTripButtons === "function" &&
      tripButtonsContainer
    ) {
      try {
        window.updateTripButtons(data.status);
      } catch (e) {
        console.error("Error calling updateTripButtons:", e);
      }
    }
  }

  function handleGenericNotification(data) {
    console.log("Manager: Handling notification:", data);
    const message =
      data.message || (typeof data === "string" ? data : JSON.stringify(data));
    alert(`Notification: ${message}`);
  }

  function handleBalanceUpdate(data) {
    console.log("Manager: Handling balance_update:", data);
    const balanceElement = document.getElementById("user-balance-display");
    if (balanceElement && data.balance !== undefined) {
      try {
        balanceElement.textContent = `€${parseFloat(data.balance).toFixed(2)}`;
      } catch (e) {
        console.error("Failed to update balance display:", e);
        balanceElement.textContent = `€ --.--`;
      }
    }
  }

  // --- ІManager Init---

  function initializeManager() {
    if (isInitialized) return;
    console.log("DOM fully loaded. Initializing WebSocket Manager...");
    isInitialized = true;

    baseTimerDisplayElement = document.getElementById("base-timer-display");
    globalTripStatusContainer = document.getElementById("global-trip-status");
    tripTimerElement = document.getElementById("trip-timer");
    tripButtonsContainer = document.getElementById("trip-buttons");
    tripSummaryContainer = document.getElementById("trip-summary-container");

    registerMessageHandler("trip_status", handleTripStatusUpdate);
    registerMessageHandler("notification", handleGenericNotification);
    registerMessageHandler("balance_update", handleBalanceUpdate);
    registerMessageHandler("internal_socket_close", (event) => {
      console.log("Manager handling internal_socket_close.");
      stopLocalTimer("Connection closed.");
    });
    registerMessageHandler("internal_socket_error", (error) => {
      console.log("Manager handling internal_socket_error.");
      stopLocalTimer("Connection error.");
    });

    initializeSharedWebSocket();

    showGlobalTripStatus(false);
    updateTimerDisplay("Connecting...");
  }

  // --- Global Manager Interface ---
  window.WebSocketManager = Object.freeze({
    initialize: initializeSharedWebSocket,
    register: registerMessageHandler,
    sendMessage: sendMessage,
  });

  // --- Start Init ---
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeManager);
  } else {
    initializeManager();
  }
})();
