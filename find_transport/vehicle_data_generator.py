import random
import json

latitude_min = 53.3
latitude_max = 53.4
longitude_min = -6.3
longitude_max = -6.2


def generate_random_coordinates():
    latitude = random.uniform(latitude_min, latitude_max)
    longitude = random.uniform(longitude_min, longitude_max)
    return latitude, longitude


objects = []
for i in range(100):
    latitude, longitude = generate_random_coordinates()
    type = random.choice(["E-Bike", "Bike", "E-Scooter"])
    status = random.choice(["True", "False"])
    battery_percentage = random.randint(0, 100) if type != "Bike" else None
    price_per_hour = random.uniform(0.5, 2.0)

    obj = {
        "id": i + 1,
        "latitude": latitude,
        "longitude": longitude,
        "type": type,
        "status": status,
        "battery_percentage": battery_percentage,
        "price_per_hour": price_per_hour,
    }
    objects.append(obj)

# Збереження об'єктів у JSON файл
with open("vehicle_data.json", "w") as json_file:
    json.dump(objects, json_file, indent=4)

print("JSON file generated and saved as 'vehicle_data.json'")
