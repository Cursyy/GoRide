let map;
let userLat, userLon;
let markers=[];
// Список категорій (рядок, розділений комами)
const categoriesList = "accommodation.hotel,accommodation.hostel,activity,airport,commercial.supermarket,commercial.marketplace,commercial.shopping_mall,commercial.elektronics,commercial.outdoor_and_sport,commercial.hobby,commercial.gift_and_souvenir,commercial.clothing,commercial.houseware_and_hardware,commercial.florist,commercial.health_and_beauty,commercial.pet,commercial.food_and_drink,commercial.gas,catering.restaurant.pizza,catering.restaurant.burger,catering.restaurant.italian,catering.restaurant.chinese,catering.restaurant.chicken,catering.restaurant.japanese,catering.restaurant.thai,catering.restaurant.steak_house,catering,education.school,education.library,education.college,education.university,entertainment,entertainment.culture,entertainment.zoo,entertainment.museum,entertainment.cinema,healthcare,healthcare.hospital,leisure,leisure.picnic,leisure.spa,leisure.park,natural,natural.forest,natural.water,national_park,office.government,railway,railway.train,railway.subway,railway.tram,railway.light_rail,rental,service,tourism,religion,amenity,beach,public_transport";

// Розділяємо рядок на масив
const categories = categoriesList.split(',');

// Створимо структуру, що групує підкатегорії за батьківською категорією
const groupedCategories = {}; // { parent: [fullValue, ...] }
const simpleCategories = []; // без крапки

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

// Функція, яка буде викликатися при натисканні на кнопку/опцію
async function  searchPlaces(value) {
    console.log("Search for:", value);
    clearMarkers();

    const response = await fetch(`/en/get_direction/api/places/${value}/${userLat}/${userLon}`);
    const data = await response.json();

    data.features.forEach(place => {
        const [lon, lat] = place.geometry.coordinates;
        const marker = L.marker([lat, lon]).addTo(map).bindPopup(place.properties.name);
        markers.push(marker);
    });
    

}
function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}
// Генеруємо HTML
let html = '';

// Спочатку кнопки для простих категорій
simpleCategories.forEach(cat => {
    html += `<button class="category-btn" onclick="searchPlaces('${cat}')">${cat}</button>`;
});

// Тепер для групованих категорій – випадаючі меню
for (const parent in groupedCategories) {
    const subcats = groupedCategories[parent];
    // Якщо більше ніж одна підкатегорія, створюємо dropdown
    if (subcats.length > 1) {
        html += `
            <div class="dropdown" style="display:inline-block; margin: 5px;">
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
        // Якщо лише одна підкатегорія, можна показати як звичайну кнопку
        html += `<button class="category-btn" onclick="searchPlaces('${subcats[0]}')">${subcats[0]}</button>`;
    }
}

// Вставляємо згенерований HTML у контейнер
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
