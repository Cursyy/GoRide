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