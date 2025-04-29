//https://www.w3schools.com/howto/howto_css_modals.asp
//code source
const originalAlert = window.alert;

window.alert = function (message) {
  showCustomAlert(message);
};

function showCustomAlert(message) {
  const alertContainer = document.createElement("div");
  alertContainer.className = "custom-alert-container";
  alertContainer.id = "myAlert";
  alertContainer.innerHTML = `
        <div class="alert-content">
            <span class="close">&times;</span>
            <p>${message}</p>
        </div>
    `;

  document.body.appendChild(alertContainer);

  var modal = document.getElementById("myAlert");
  var span = modal.getElementsByClassName("close")[0];

  span.onclick = function () {
    modal.style.display = "none";
  };

  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  };

  modal.style.display = "block";
}
