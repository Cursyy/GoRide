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
});
        

async function fetchTripStatus() {
    const res = await fetch("/get_direction/api/trip_status/");
    const data = await res.json();
    const tripTimer = document.getElementById("trip-timer");

    if (data.status === "active") {
        // обраховуємо таймер як: total_travel_time + (now - started_at)
        const now = new Date();
        const startedAt = new Date(data.started_at);
        const elapsedTime = now - startedAt + data.total_travel_time * 1000; // total_travel_time у секундах, перетворюємо в мілісекунди

        const hours = String(Math.floor(elapsedTime / (1000 * 60 * 60))).padStart(2, '0');
        const minutes = String(Math.floor((elapsedTime % (1000 * 60 * 60)) / (1000 * 60))).padStart(2, '0');
        const seconds = String(Math.floor((elapsedTime % (1000 * 60)) / 1000)).padStart(2, '0');
        
        tripTimer.textContent = `${hours}:${minutes}:${seconds}`;
    } else if (data.status === "paused") {
        // зупинити таймер, показати total_travel_time
        const hours = String(Math.floor(data.total_travel_time / 3600)).padStart(2, '0');
        const minutes = String(Math.floor((data.total_travel_time % 3600) / 60)).padStart(2, '0');
        const seconds = String(Math.floor(data.total_travel_time % 60)).padStart(2, '0');
        
        tripTimer.textContent = `${hours}:${minutes}:${seconds}`;
    } else {
        // приховати таймер або скинути
        tripTimer.textContent = "00:00:00";
    }
}

setInterval(fetchTripStatus, 500);