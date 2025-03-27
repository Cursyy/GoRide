let map;
let userLat, userLon;
let markers=[];
let waypoints = [];
let route;
let turnByTurnLayer;
let userMarkersCount;
const categoriesList = "accommodation.hotel,accommodation.hostel,activity,airport,commercial.supermarket,commercial.marketplace,commercial.shopping_mall,commercial.elektronics,commercial.outdoor_and_sport,commercial.hobby,commercial.gift_and_souvenir,commercial.clothing,commercial.houseware_and_hardware,commercial.florist,commercial.health_and_beauty,commercial.pet,commercial.food_and_drink,commercial.gas,catering.restaurant.pizza,catering.restaurant.burger,catering.restaurant.italian,catering.restaurant.chinese,catering.restaurant.chicken,catering.restaurant.japanese,catering.restaurant.thai,catering.restaurant.steak_house,catering,education.school,education.library,education.college,education.university,entertainment,entertainment.culture,entertainment.zoo,entertainment.museum,entertainment.cinema,healthcare,healthcare.hospital,leisure,leisure.picnic,leisure.spa,leisure.park,natural,natural.forest,natural.water,national_park,office.government,railway,railway.train,railway.subway,railway.tram,railway.light_rail,rental,service,tourism,religion,amenity,beach,public_transport";


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

async function  searchPlaces(value) {
    clearMarkers();

    const response = await fetch(`/en/get_direction/api/places/${value}/${userLat}/${userLon}`);
    const data = await response.json();

    data.features.forEach(place => {
        const [lon, lat] = place.geometry.coordinates;
        const marker = L.marker([lat, lon]).addTo(map).bindPopup(place.properties.name);
        markers.push(marker);
        marker.on('click', () => {
            waypoints.push([lat,lon]);
            createButton("get-direction-button","Get Direction");
        });
    });
    

}
const turnByTurnMarkerStyle = {
    radius: 5,
    fillColor: "#fff",
    color: "#0E6655",
    weight: 1,
    opacity: 1,
    fillOpacity: 1
  }
  
  async function getRoute(waypoints) {
    clearRoute();
    waypoints.push([userLat, userLon]);
    try {
        console.log("Відправляємо waypoints:", waypoints);
        
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
    createButton("get-direction-button","Get Direction");
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
    map = L.map('map').setView([53.347854,-6.259504], 13);
    L.tileLayer('https://maps.geoapify.com/v1/tile/klokantech-basic/{z}/{x}/{y}.png?apiKey=d16fda76e6fc4822bbc407474c620a8e', {
        attribution: 'Powered by <a href="https://www.geoapify.com/" target="_blank">Geoapify</a> | <a href="https://openmaptiles.org/" target="_blank">© OpenMapTiles</a> <a href="https://www.openstreetmap.org/copyright" target="_blank">© OpenStreetMap</a> contributors',
        maxZoom: 20, id: 'osm-bright'
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


function createButton(buttonId, buttonText) {
    let button = document.getElementById(buttonId);

    if (!button) {
        button = document.createElement("button");
        button.id = buttonId;
        button.textContent = buttonText;

        document.body.appendChild(button);
    }

    button.onclick = null;

    button.addEventListener("click", function() {
        if (buttonId === "get-direction-button") {
            getRoute(waypoints);
        } else if (buttonId === "delete-markers-button") {
            clearMarkers();
            clearRoute();
            document.getElementById("get-direction-button").remove()
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
        createButton("add-stops-button", "Add more stops");
        createButton("delete-markers-button", "Delete my markers");
    } catch (error) {
        console.error("Error:", error);
    }
});