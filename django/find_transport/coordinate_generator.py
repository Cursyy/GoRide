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
for i in range(20):
    latitude, longitude = generate_random_coordinates()
    max_spaces = random.randint(1, 20)
    obj = {
        "id": i + 1,
        "latitude": latitude,
        "longitude": longitude,
        "max_spaces": max_spaces,
    }
    objects.append(obj)

# Збереження об'єктів у JSON файл
with open("EV_stations.json", "w") as json_file:
    json.dump(objects, json_file, indent=4)

print("JSON file generated and saved as 'EV_stations.json'")
