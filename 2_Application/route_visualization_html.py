import requests
import io
import csv

# get all containers
def fetch_containers(base_url):
    response = requests.get(base_url + "/containers")
    return response.json()

# get all routes by container_id
def fetch_routes(base_url, container_id):
    response = requests.get(base_url + f"/containers/{container_id}/routes")
    return response.json()

# get csv by route_id and container_id
def fetch_csv(base_url, container_id, route_id):
    response = requests.get(base_url + f"/containers/{container_id}/routes/{route_id}")
    rows = list(csv.reader(io.StringIO(response.text)))
    return rows

def get_color(temp, humidity):
    if temp >= 25 and humidity >= 80:
        return simplekml.Color.red
    elif temp >= 25:
        return simplekml.Color.orange
    elif humidity >= 80:
        return simplekml.Color.yellow
    else:
        return simplekml.Color.blue

def build_segments(rows):
    segments = []
    current_color = None
    current_coords = []

    for row in rows:
        temp = float(row[3])
        humidity = float(row[4])
        color = get_color(temp, humidity)
        coord = (float(row[2]), float(row[1]))

        if color != current_color:
            if current_coords:
                segments.append((current_color, current_coords))
                current_coords = [current_coords[-1]]
            current_color = color

        current_coords.append(coord)

    if current_coords:
        segments.append((current_color, current_coords))

    return segments

