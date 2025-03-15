let currentStation = null;
let userLat = null;
let userLon = null;
let activeRequest = null;
document.addEventListener("DOMContentLoaded", function() {
    loadStations();
    loadVehicles();

    const batteryFilter = document.getElementById("battery-filter");
    const typeFilter = document.getElementById("type-filter");
    
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
        userLat = position.coords.latitude;
        userLon = position.coords.longitude;
        if (map) {
            map.setView([userLat, userLon], 15);
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
            currentStation = station.id;
            loadVehicles(station.id);
            createButton(station.id);
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

function createButton(){
    let button = document.getElementById("get-direction-button");

    if (!button) {
        button = document.createElement("button");
        button.id = "get-direction-button";
        button.textContent = "Get Direction";

        button.style.position = "absolute";
        button.style.top = "300px";
        button.style.left = "50px";
        button.style.zIndex = "1000";

        document.body.appendChild(button);
    }


    button.onclick = null;

    button.addEventListener("click", function() {
        console.log(currentStation)
        getDirection(currentStation);
    });
}

async function getDirection(stationId=null){
try{
    const response = await fetch(`api/stations?id=${stationId}`);
    if(!response.ok){
        console.error("Error fetching station",response.status)
        return;
    }

    const data = await response.json();
    const station = data.station
    if (!station || !station.latitude || !station.longitude) {
        console.error("Invalid station data:", station);
        return;
    }

    if(activeRequest){
        activeRequest.abort();
    }
    activeRequest = new XMLHttpRequest();

    activeRequest.open('GET', `https://api.openrouteservice.org/v2/directions/driving-car?api_key=5b3ce3597851110001cf6248fc631c4ebfff476ba2813120ea71d4e2&start=${userLon},${userLat}&end=${station.longitude},${station.latitude}`);

    activeRequest.setRequestHeader('Accept', 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8');

    activeRequest.onreadystatechange = function () {
    if (this.readyState === 4) {
        console.log('Status:', this.status);
        console.log('Headers:', this.getAllResponseHeaders());
        console.log('Body:', this.responseText);
        activeRequest=null;
    }
    };

    activeRequest.send();
    } catch (error) {
        console.error("Error in getDirection:", error);
    }
}