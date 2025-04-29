console.log("reviewPopup.js loaded!");

function showReviewPopup() {
  console.log("showReviewPopup called!");
  if (document.getElementById("review-popup")) {
    return;
  }

  const overlay = document.createElement("div");
  overlay.id = "review-overlay";
  overlay.style.position = "fixed";
  overlay.style.top = "0";
  overlay.style.left = "0";
  overlay.style.width = "100%";
  overlay.style.height = "100%";
  overlay.style.backgroundColor = "rgba(0, 0, 0, 0.5)";
  overlay.style.zIndex = "999";

  const popup = document.createElement("div");
  popup.id = "review-popup";
  popup.className = "card p-4";
  popup.style.position = "fixed";
  popup.style.top = "50%";
  popup.style.left = "50%";
  popup.style.transform = "translate(-50%, -50%)";
  popup.style.zIndex = "1000";
  popup.style.maxWidth = "400px";
  popup.style.width = "90%";

  popup.innerHTML = `
        <h3 class="card-title text-center mb-4">${gettext("Leave a Review")}</h3>
        <div id="rating-stars" class="text-center mb-4">
            <span class="star" data-value="1">★</span>
            <span class="star" data-value="2">★</span>
            <span class="star" data-value="3">★</span>
            <span class="star" data-value="4">★</span>
            <span class="star" data-value="5">★</span>
        </div>
        <textarea id="review-text" class="form-control mb-4" placeholder=${gettext("Write your review...")} style="height: 100px;"></textarea>
        <div class="d-flex justify-content-center gap-2">
            <button id="submit-review-btn" class="btn btn-success">${gettext("Submit")}</button>
            <button id="close-review-btn" class="btn btn-danger">${gettext("Close")}</button>
        </div>
    `;

  document.body.appendChild(overlay);
  document.body.appendChild(popup);

  const stars = document.querySelectorAll(".star");
  let selectedRating = 5;
  stars.forEach((star) => {
    star.style.cursor = "pointer";
    star.style.fontSize = "24px";
    star.style.color = "#ccc";
    if (star.getAttribute("data-value") <= selectedRating) {
      star.style.color = "#ffd700";
    }

    star.addEventListener("click", () => {
      selectedRating = parseInt(star.getAttribute("data-value"));
      stars.forEach((s) => {
        s.style.color =
          s.getAttribute("data-value") <= selectedRating ? "#ffd700" : "#ccc";
      });
    });
  });

  document.getElementById("submit-review-btn").addEventListener("click", () => {
    const reviewText = document.getElementById("review-text").value.trim();
    if (!reviewText) {
      Toastify({
        text: `${gettext("Please write a review before submitting.")}`,
        duration: 3000,
        style: { background: "#dc3545" },
      }).showToast();
      return;
    }

    const csrfToken = document.querySelector(
      "[name=csrfmiddlewaretoken]",
    ).value;
    const reviewData = { text: reviewText, rating: selectedRating };
    console.log("Sending review with data:", reviewData);
    const currentPath = window.location.pathname;
    const languagePrefix = currentPath.split("/")[1];
    const submitUrl = `/${languagePrefix}/reviews/submit/`;
    console.log("Submitting to URL:", submitUrl);

    fetch(submitUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
        "Cache-Control": "no-cache",
      },
      body: JSON.stringify(reviewData),
    })
      .then((response) => {
        console.log("Response status:", response.status);
        return response.json();
      })
      .then((data) => {
        console.log("Response data:", data);
        if (data.success) {
          Toastify({
            text: `${gettext("Thank you for your review!")}`,
            duration: 3000,
            style: { background: "#28a745" },
          }).showToast();
          overlay.remove();
          popup.remove();
        } else {
          Toastify({
            text: `${gettext("Error submitting review. Please try again.")}`,
            duration: 3000,
            style: { background: "#dc3545" },
          }).showToast();
        }
      })
      .catch((error) => {
        console.error("Error submitting review:", error);
        Toastify({
          text: `${gettext("Error submitting review. Please try again.")}`,
          duration: 3000,
          style: { background: "#dc3545" },
        }).showToast();
      });
  });

  document.getElementById("close-review-btn").addEventListener("click", () => {
    overlay.remove();
    popup.remove();
  });
}

window.showReviewPopup = showReviewPopup;
console.log("window.showReviewPopup defined!");
