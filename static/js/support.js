(function () {
  "use strict";

  let chatId = null;
  let messagesContainer = null;
  let textarea = null;
  let form = null;
  let notificationSound = null;

  // --- UI---
  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  function addNewMessage(messageHtml) {
    if (messagesContainer) {
      messagesContainer.insertAdjacentHTML("beforeend", messageHtml);
      scrollToBottom();
    } else {
      console.error(
        "Support: Cannot add message, messagesContainer not found.",
      );
    }
  }

  // --- WebSocket Messages Handlers (chat) ---
  function handleChatMessage(data) {
    console.log("Support: Handling chat_message:", data);
    if (!data || !data.user || !data.message || !data.created_at) {
      console.error("Support: Received incomplete chat message data:", data);
      return;
    }

    if (messagesContainer) {
      const messageHtml = `
                 <div class="mb-3">
                     <strong style="color: #0E6655;">${data.user}:</strong>
                     <p>${data.message}</p> <small class="text-muted">${data.created_at}</small>
                 </div>
             `;
      addNewMessage(messageHtml);

      const content = data.message || "";

      if (notificationSound) {
        notificationSound
          .play()
          .catch((error) =>
            console.error("Support: Audio play failed:", error),
          );
      }
    } else {
      console.log("Support: Received chat message, but not on a chat page.");
    }
  }

  function handleChatJoined(data) {
    console.log(`Support: Successfully joined chat: ${data.chat_id}`);
  }

  function handleChatLeft(data) {
    console.log(`Support: Left chat: ${data.chat_id}`);
  }

  function handleServerError(data) {
    console.error(`Support: Received server error: ${data.message}`);
    alert(`Chat Error: ${data.message}`);
  }

  // --- Chat Init Logic---
  function initializeChatLogic() {
    console.log("Support: Initializing chat logic...");
    messagesContainer = document.getElementById("messages");
    textarea = document.querySelector(".chat-form textarea");
    form = document.getElementById("form");
    notificationSound = document.getElementById("notification-sound");

    if (!messagesContainer) {
      console.log("Support: Messages container not found, chat UI disabled.");
      return;
    }

    chatId = messagesContainer.dataset.chatId;
    console.log("Support: Chat ID found:", chatId);

    if (textarea) {
      textarea.addEventListener("input", () => {
        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
      });
    }

    if (form) {
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        if (!textarea) return;
        let message = textarea.value.trim();
        if (!message) return;

        console.log("Support: Attempting to send message:", message);

        if (chatId) {
          const success = WebSocketManager.sendMessage("send_chat_message", {
            message: message,
            chat_id: chatId,
          });
          if (success) {
            form.reset();
            textarea.style.height = "auto";
          } else {
            alert("Failed to send message. Connection might be down.");
          }
        } else {
          console.error("Support: Cannot send message: chatId is missing.");
          alert("Error: Chat ID is missing.");
        }
      });
    } else {
      console.log("Support: Chat form not found.");
    }

    if (window.WebSocketManager) {
      console.log("Support: Registering handlers with WebSocketManager.");
      WebSocketManager.register("chat_message", handleChatMessage);
      WebSocketManager.register("chat_joined", handleChatJoined);
      WebSocketManager.register("chat_left", handleChatLeft);
      WebSocketManager.register("error", handleServerError);

      const joinChatRoom = () => {
        console.log("Support: Socket open event received, attempting join.");
        if (chatId) {
          WebSocketManager.sendMessage("join_chat", { chat_id: chatId });
        } else {
          console.error(
            "Support: Cannot join chat: chatId is missing when socket opened.",
          );
        }
      };

      WebSocketManager.register("internal_socket_open", joinChatRoom);

      const currentSocket = WebSocketManager.getSocket
        ? WebSocketManager.getSocket()
        : null;
      if (currentSocket && currentSocket.readyState === WebSocket.OPEN) {
        console.log("Support: Socket already open on init, attempting join.");
        joinChatRoom();
      }
    } else {
      console.error("Support: WebSocketManager not found! Load order issue?");
    }

    scrollToBottom();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeChatLogic);
  } else {
    initializeChatLogic();
  }
})();
