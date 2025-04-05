let map;
let userLat, userLon;
let markers=[];
let waypoints = [];
let route;
let turnByTurnLayer;
let userMarkersCount;
const categoriesList = "accommodation,activity,airport,commercial,catering,education,entertainment,healthcare,leisure,natural,national_park,railway,service,tourism,religion,amenity,beach,public_transport";


const categories = categoriesList.split(',');

const groupedCategories = {};
const simpleCategories = [];




categories.forEach(cat => {
    if (cat.indexOf('.') === -1) {
        simpleCategories.push(cat);
    } else {
        const parts = cat.split('.');
        const parent = parts[0];
        if (!groupedCategories[parent]) {
            groupedCategories[parent] = [];
        }
        groupedCategories[parent].push(cat);
    }
});
function renderResults(results) {
    const resultsContainer = document.getElementById('places-container');
    resultsContainer.innerHTML = '';

    results.forEach(result => {
        let resultHTML = `
            <div class="result-item">
                    <div class="result-content">
                        <h5 class="result-title">${result.name || 'No name available'}</h5>
                        <p><strong>Address:</strong> ${result.address_line2 || ''}</p>
                        <p><strong>Distance:</strong> ${result.distance} meters</p>
                        <p><strong>Estimated Time:</strong> ${Math.ceil(result.distance / 5.5 / 60)} minutes</p>
                    </div>
                </div>
        `;
        resultsContainer.innerHTML += resultHTML;
    });
}

function renderCategories() {
    const categoriesContainer = document.getElementById('categories-container');
    let html = '';

    simpleCategories.forEach(cat => {
        html += `
            <li>
                <a class="dropdown-item" href="#" onclick="searchPlaces('${cat}'); return false;">${cat}</a>
            </li>`;
    });

    categoriesContainer.innerHTML = html;
}


async function searchLocations() {
    const searchInput = document.getElementById('search-input').value;
    console.log('Searching for:', searchInput);

    clearMarkers();

    const response = await fetch(`/en/get_direction/api/search/${searchInput}/`);
    const data = await response.json();
    console.log(data)

    const results = data.results.map(result => ({
        name: result.name,
        address_line1: result.address_line1,
        address_line2: result.address_line2,
        distance: result.distance,
        distance_units: result.properties?.distance_units,
        time: result.properties?.time,
        lat: result.lat,
        lon: result.lon
    }));

    renderResults(results);

    data.results.forEach(result=> {
        if(result.rank.confidence > 0.5 ){
            const lon= result.lon;
            const lat = result.lat;
            const marker = L.marker([lat, lon]).addTo(map).bindPopup(result.formatted);
            markers.push(marker);
            marker.on('click', () => {
            waypoints.push([lat,lon]);
            createButton("get-direction-button","Get Direction");
        });
        }
    })
}


async function  searchPlaces(value) {
    clearMarkers();

    const response = await fetch(`/en/get_direction/api/places/${value}/${userLat}/${userLon}`);
    const data = await response.json();
    console.log(data)
    const results = data.features.map(result => ({
        name: result.properties?.name, 
        address_line1: result.properties?.address_line1,
        address_line2: result.properties?.address_line2,
        distance: result.properties?.distance,
        distance_units: result.properties?.distance_units,
        time: result.properties?.time ? result.properties.time : null,
        lat: result.lat,
        lon: result.lon
    }));

    renderResults(results);
    data.features.forEach(place => {
        const [lon, lat] = place.geometry.coordinates;
        const marker = L.marker([lat, lon]).addTo(map).bindPopup(`
            ${place.properties.address_line1}<br>
            ${place.properties.address_line2}
        `);
        markers.push(marker);
        marker.on('click', () => {
            waypoints.push([lat,lon]);
            createButton("get-direction-button","Get Direction");
        });
    });
    

}

if (!document.getElementById('results-container')) {
    const resultsContainer = document.createElement('div');
    resultsContainer.id = 'results-container';
    document.body.appendChild(resultsContainer)
}

  async function getRoute(waypoints) {
    clearRoute();
    waypoints.push([userLat, userLon]);
    try {
        console.log("Send waypoints:", waypoints);
        
        const response = await fetch(`/en/get_direction/api/route/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ waypoints: waypoints }),
        });

        if (!response.ok) throw new Error("Failed to fetch route");

        const result = await response.json();
        route = L.geoJSON(result, {
            style: (feature) => ({
                color: "rgba(20, 137, 255, 0.7)",
                weight: 5
            })
        }).bindPopup((layer) => {
            return `${layer.feature.properties.distance} ${layer.feature.properties.distance_units}, ${layer.feature.properties.time}`;
        }).addTo(map);
        
         turnByTurns = [];

        result.features.forEach(feature => {
            feature.properties.legs.forEach((leg, legIndex) => {
                leg.steps.forEach(step => {
                    if (step.instruction && step.instruction.text) {
                        turnByTurns.push({
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": feature.geometry.coordinates[legIndex][step.from_index]
                            },
                            "properties": {
                                "instruction": step.instruction.text
                            }
                        });
                    } 
                });
            });
        });

        if (turnByTurns.length > 0) {
            turnByTurnLayer = L.geoJSON({
                type: "FeatureCollection",
                features: turnByTurns
            }, {
                pointToLayer: (feature, latlng) => {
                    return L.circleMarker(latlng, {
                        radius: 5,
                        color: "#FF5733"
                    });
                }
            }).bindPopup((layer) => `${layer.feature.properties.instruction}`).addTo(map);
        } else {
            console.warn("There are no available turns to show.");
        }

    } catch (err) {
        console.error("Error fetching route:", err);
    }
}

function clearRoute(){
    if (route) {
        map.removeLayer(route);
        route = null;
    }

    if (turnByTurnLayer) {
        map.removeLayer(turnByTurnLayer);
        turnByTurnLayer = null;
    }

    waypoints = [];
    createButton("get-direction","Get Direction");
}
function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

let html = '';


simpleCategories.forEach(cat => {
    html += `<button class="category-btn" onclick="searchPlaces('${cat}')">${cat}</button>`;
});


for (const parent in groupedCategories) {
    const subcats = groupedCategories[parent];

    if (subcats.length > 1) {
        html += `
            <div class="dropdown" style="display:inline-block;">
                <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdown-${parent}" data-bs-toggle="dropdown" aria-expanded="false">
                    ${parent}
                </button>
                <ul class="dropdown-menu" aria-labelledby="dropdown-${parent}">`;
        subcats.forEach(subcat => {
            html += `<li><a class="dropdown-item" href="#" onclick="searchPlaces('${subcat}'); return false;">${subcat}</a></li>`;
        });
        html += `</ul>
            </div>`;
    } else {

        html += `<button class="category-btn" onclick="searchPlaces('${subcats[0]}')">${subcats[0]}</button>`;
    }
}

document.getElementById('categories-container').innerHTML = html;

if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition, showError);
} else {
    console.log("Geolocation is not supported by this browser.");
}

function initializeMap() {
    map = L.map('map').setView([53.347854, -6.259504], 13);
    L.tileLayer('https://maps.geoapify.com/v1/tile/klokantech-basic/{z}/{x}/{y}.png?apiKey=d16fda76e6fc4822bbc407474c620a8e', {
        attribution: 'Powered by <a href="https://www.geoapify.com/" target="_blank">Geoapify</a>',
        maxZoom: 20
    }).addTo(map);
}
initializeMap();

function showPosition(position) {
    let button = document.getElementById("userLocation");
    button.addEventListener("click", function() {
        userLat = position.coords.latitude;
        userLon = position.coords.longitude;
        if (map) {
            map.setView([userLat, userLon], 15);
        }});
        if (window.userMarker) {
                window.userMarker.setLatLng([userLat, userLon]);
        } else {
                let userIcon = L.icon({
                    iconUrl: '/static/images/you_are_here.png',
                    iconSize: [38, 50],
                    iconAnchor: [22, 38],
                    popupAnchor: [-3, -38]
                });
                window.userMarker = L.marker([userLat, userLon], { icon: userIcon })
                    .bindPopup("You are here")
                    .openPopup()
                    .addTo(map);
        }
        
}

function showError(error) {
    console.error("Error getting location:", error.message);
}

if (navigator.geolocation) {
    navigator.geolocation.watchPosition(showPosition, showError, {
        enableHighAccuracy: true,
        maximumAge: 0
    });
} else {
    console.log("Geolocation is not supported by this browser.");
}

function createButton(buttonId, buttonText) {
    let button = document.getElementById(buttonId);

    if (!button) {
        button = document.createElement("button");
        button.id = buttonId;
        button.textContent = buttonText;
        button.classList.add("map-button");
    }

    button.onclick = null;

    button.addEventListener("click", function() {
        if (buttonId === "get-direction") {
            getRoute(waypoints);
        } else if (buttonId === "delete-markers-button") {
            clearMarkers();
            clearRoute();
        } else if (buttonId === "add-stops-button") {
            map.on('dblclick', async (e) => {
                const { lat, lng } = e.latlng;
                try {
                    const response = await fetch(`/en/get_direction/api/get_address_marker/${lat}/${lng}`);
                    if (!response.ok) throw new Error("Can't find address.");
                    const data = await response.text();
                    const marker = L.marker([lat, lng]).addTo(map).bindPopup(data).openPopup();
                    markers.push(marker);
                    waypoints.push([lat, lng]);

                    if (waypoints.length > 1) {
                        getRoute(waypoints);
                    }
                    createButton("add-stops-button", "Add more stops");
                    createButton("delete-markers-button", "Delete my markers");
                } catch (error) {
                    console.error("Error:", error);
                }
            });
        }
    });

    return button;
}

function addMapControls() {
    const controlDiv = L.control({ position: 'topleft' });

    controlDiv.onAdd = function() {
        const container = L.DomUtil.create('div', 'map-buttons-container');
        container.appendChild(createButton("get-direction", "Get Directions"));
        container.appendChild(createButton("add-stops-button", "Add more stops"));
        container.appendChild(createButton("delete-markers-button", "Delete my markers"));
        return container;
    };

    controlDiv.addTo(map);
}

map.on('dblclick', async (e) => {
    const { lat, lng } = e.latlng;
    try {
        const response = await fetch(`/en/get_direction/api/get_address_marker/${lat}/${lng}`);
        if (!response.ok) throw new Error("Can't find address.");
        const data = await response.text();

        const marker = L.marker([lat, lng]).addTo(map).bindPopup(data).openPopup();
        markers.push(marker);
        waypoints.push([lat, lng]);

        if (waypoints.length > 1) {
            getRoute(waypoints);
        }
    } catch (error) {
        console.error("Error:", error);
    }
});

addMapControls();

document.addEventListener('DOMContentLoaded', renderCategories);