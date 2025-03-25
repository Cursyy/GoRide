let currentStation = null;
let userLat = null;
let userLon = null;
let activeController = null;
let routeLayer = null;
let map = null;
let price = null;
let voucher = false;
document.addEventListener("DOMContentLoaded", function() {
    loadStations();
    loadVehicles();

    const batteryFilter = document.getElementById("battery-filter");
    const typeFilter = document.getElementById("type-filter");

    if (!batteryFilter || !typeFilter) {
        console.error("battery-filter або type-filter не знайдено у DOM.");
        return;
    }

    batteryFilter.addEventListener("input", function() {
        document.getElementById("battery-filter").innerText = batteryFilter.value;
        loadVehicles(currentStation);
    });

    typeFilter.addEventListener("change",function(){ loadVehicles(currentStation)});

    

});

document.addEventListener("submit", async function(event) {
    if (!event.target.matches(".voucher-form")) return;

    event.preventDefault();

    console.log("Form submitted!");

    const form = event.target;
    const vehicleId = form.getAttribute("data-vehicle-id");
    const voucherCode = form.querySelector("input[name='voucher']").value;
    const voucherType = form.querySelector("input[name='voucher_type']").value;

    console.log({
        vehicle_id: vehicleId,
        code: voucherCode,
        type: voucherType
    });

    try {
        const response = await fetch(`api/voucher`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                vehicle_id: vehicleId,
                code: voucherCode,
                type: voucherType
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert(`Voucher applied successfully. New price: €${data.price}`);
            price = data.price;
            voucher = true;
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error("Error applying voucher:", error);
        alert("Something went wrong. Please try again.");
    }
});
function getCookie(name){
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function loadStations() {
    const response = await fetch('api/stations');
    let stations = await response.json();

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError);
    } else {
        console.log("Geolocation is not supported by this browser.");
    }


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
    batteryFilter = parseInt(document.getElementById("battery-filter").value);
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
        vehicleCard.classList.add('w-100');
        vehicleCard.classList.add('row');

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
            <div class="left-part col-12 col-lg-8">
                <div class="vehicle-image"><img src="${imgSrc}" alt="${vehicle.type} image"/></div>
                <div class="vehicle-details">
                    <h3>${vehicle.type}</h3>
                    ${vehicle.battery_percentage !== null ? `<p>Battery: ${vehicle.battery_percentage}%</p>` : ""}
                    <a href="https://www.google.com/maps?q=${vehicle.latitude},${vehicle.longitude}" target="_blank">Show on Map</a>
                </div>
            </div>
            <div class="vehicle-price col-12 col-lg-4">
                <form class="voucher-form" data-vehicle-id="${vehicle.id}">
                    <label for="voucher-${vehicle.id}">Voucher code:</label>
                    <input type="text" id="voucher-${vehicle.id}" name="voucher" placeholder="Enter voucher code">
                    <input type="hidden" name="voucher_type" value="vehicle">
                    <button type="submit">Apply</button>
                </form>
                <p>Price per hour: €${vehicle.price_per_hour}</p>
                <a href="/booking/rent/${vehicle.id}/" class="btn btn-primary">Rent</a>
            </div>
        `;
        container.appendChild(vehicleCard);
    });
}

function rentVehicle(vehicleId) {
    window.location.href = `/booking/Rent/${vehicleId}/`;
}

function createButton(){
    let button = document.getElementById("get-direction-button");

    if (!button) {
        button = document.createElement("button");
        button.id = "get-direction-button";
        button.textContent = "Get Direction";

        document.body.appendChild(button);
    }


    button.onclick = null;

    button.addEventListener("click", function() {
        console.log(currentStation)
        getDirection(currentStation);
    });
}

async function getDirection(stationId = null) {
    try {
        if (activeController) {
            activeController.abort();
        }

        activeController = new AbortController();
        const stationSignal = activeController.signal;

        const response = await fetch(`api/stations?id=${stationId}`, { signal: stationSignal });
        if (!response.ok) {
            console.error("Error fetching station", response.status);
            return;
        }

        const data = await response.json();
        const station = data.station;

        if (!station || !station.latitude || !station.longitude) {
            console.error("Invalid station data:", station);
            return;
        }

        const directionController = new AbortController();
        const directionSignal = directionController.signal;

        const api_response = await fetch(`api/get_direction/${station.id}/${userLon}/${userLat}`, { signal: directionSignal });

        if (!api_response.ok) {
            console.error("Error fetching direction", api_response.status);
            return;
        }

        const api_data = await api_response.json();
        console.log(api_data);

        const coordinates = api_data.features[0].geometry.coordinates;
        drawRouteOnMap(coordinates, userLat, userLon);

    } catch (error) {
        if (error.name === 'AbortError') {
            console.log("Previous request aborted");
        } else {
            console.error("Error in getDirection:", error);
        }
    }
}
function drawRouteOnMap(coordinates, userLat, userLon) {
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }

    const latLngs = coordinates.map(coord => [coord[1], coord[0]]);

    routeLayer = L.polyline(latLngs, { color: 'blue' });

    if (map) {
        routeLayer.addTo(map);
        map.fitBounds(routeLayer.getBounds());
    } else {
        console.error("Map is not initialized");
    }
}
