document.addEventListener("DOMContentLoaded", function() {
    loadStations();
    loadVehicles();

    const batteryFilter = document.getElementById("battery-filter");
    const typeFilter = document.getElementById("type-filter");
    let currentStation = null;
    console.log(currentStation)
    batteryFilter.addEventListener("input", function() {
        document.getElementById("battery-value").innerText = this.value;
        loadVehicles(currentStation);
    });

    typeFilter.addEventListener("change",function(){ loadVehicles(currentStation)});
});

async function loadStations() {
    const response = await fetch('api/stations');
    let stations = await response.json();

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError);
    } else {
        console.log("Geolocation is not supported by this browser.");
    }

    let map;

    function initializeMap() {
        map = L.map('map').setView([53.347854,-6.259504], 13);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
    }
    initializeMap();

    function showPosition(position) {
        let userLat = position.coords.latitude;
        let userLon = position.coords.longitude;
        if (map) {
            map.setView([userLat, userLon], 15);
            setTimeout(() => {
                let userIcon = L.icon({
                    iconUrl: '/static/images/you_are_here.png',
                    iconSize: [38, 50],
                    iconAnchor: [22, 38],
                    popupAnchor: [-3, -38]
                });
                L.marker([userLat, userLon], { icon: userIcon })
                    .bindPopup("You are here")
                    .openPopup()
                    .addTo(map);
            });
        } else {
            console.error("Map is not initialized yet");
        }
    }

    function showError(error) {
        console.log("Error getting location:", error.message);
    }

    stations.forEach(station => {
        let stationIcon = L.icon({
            iconUrl: '/static/images/map-marker-2-64.png',
            iconSize: [32, 32],
            iconAnchor: [22, 38],
            popupAnchor: [-3, -38]
        });
        let marker = L.marker([station.latitude, station.longitude], { icon: stationIcon })
            .bindPopup(`<b>Max spaces:</b> ${station.max_spaces}<br><b>Free spaces:</b> ${station.free_spaces}<br>${station.address}`)
            .openPopup()
            .addTo(map);
        marker.on('click', function() {
            loadVehicles(station.id);
        });
    });
}

async function loadVehicles(stationId = null) {
    const response = await fetch('api/vehicles');
    let vehicles = await response.json();
    const typeFilter = document.getElementById("type-filter").value;
    const batteryFilter = parseInt(document.getElementById("battery-filter").value);
    vehicles = vehicles.filter(v =>
        (typeFilter === "" || v.type === typeFilter) &&
        (v.battery_percentage === null || v.battery_percentage >= batteryFilter)
    );
    if (stationId) {
        vehicles = vehicles.filter(v => (v.station_id === stationId)&&
        (typeFilter === "" || v.type === typeFilter) &&
        (v.battery_percentage === null || v.battery_percentage >= batteryFilter));
    }
    const container = document.getElementById("vehicle-container");
    container.innerHTML = "";

    vehicles.forEach(vehicle => {
        const vehicleCard = document.createElement('div');
        vehicleCard.classList.add('vehicle-card');

        let imgSrc;
        switch (vehicle.type) {
            case "Bike":
                imgSrc = '/static/images/bike.webp';
                break;
            case "E-Bike":
                imgSrc = '/static/images/e-bike.jpg';
                break;
            case "E-Scooter":
                imgSrc = '/static/images/e-scooter.jpg';
                break;
            default:
                imgSrc = '/static/images/placeholder.jpg';
        }

        vehicleCard.innerHTML = `
            <div class="vehicle-image"><img src="${imgSrc}" alt="${vehicle.type} image"/></div>
            <div class="vehicle-details">
                <h3>${vehicle.type}</h3>
                ${vehicle.battery_percentage !== null ? `<p>Battery: ${vehicle.battery_percentage}%</p>` : ""}
                <a href="https://www.google.com/maps?q=${vehicle.latitude},${vehicle.longitude}" target="_blank">Show on Map</a>
            </div>
            <div class="vehicle-price">
                <p>Price per hour: €${vehicle.price_per_hour}</p>
                <form method="get" action="/stripe_payment/${vehicle.id}/">
                    <input type="number" name="hours" min="1" value="1" class="hours-input">
                    <button type="submit" class="rent-button">Pay with Stripe</button>
                </form>
                <form method="get" action="/paypal_payment/${vehicle.id}/">
                    <input type="number" name="hours" min="1" value="1" class="hours-input">
                    <button type="submit" class="rent-button">Pay with PayPal</button>
                </form>
            </div>
        `;
        container.appendChild(vehicleCard);
    });
}