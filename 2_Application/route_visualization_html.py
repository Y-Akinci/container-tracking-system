import requests
import io
import csv
import folium
from pathlib import Path
import webbrowser

BASE_URL = "https://fl-17-240.zhdk.cloud.switch.ch"
SCRIPT_DIR = Path(__file__).parent
HTML_PATH = SCRIPT_DIR / "karte.html"

# get all containers
def fetch_containers(BASE_URL):
    response = requests.get(BASE_URL + "/containers")
    return response.json()

# get all routes by container_id
def fetch_routes(BASE_URL, container_id):
    response = requests.get(BASE_URL + f"/containers/{container_id}/routes")
    return response.json()

# get csv by route_id and container_id
def fetch_csv(BASE_URL, container_id, route_id):
    response = requests.get(BASE_URL + f"/containers/{container_id}/routes/{route_id}")
    rows = list(csv.reader(io.StringIO(response.text)))
    return rows

def get_color(temp, humidity):
    if temp >= 25 and humidity >= 80:
        return "red"
    elif temp >= 25:
        return "orange"
    elif humidity >= 80:
        return "yellow"
    else:
        return "blue"

def build_segments(rows):
    segments = []
    current_color = None
    current_coords = []

    for row in rows:
        temp = float(row[3])
        humidity = float(row[4])
        color = get_color(temp, humidity)
        coord = (float(row[1]), float(row[2]))

        if color != current_color:
            if current_coords:
                segments.append((current_color, current_coords))
                current_coords = [current_coords[-1]]
            current_color = color

        current_coords.append(coord)

    if current_coords:
        segments.append((current_color, current_coords))

    return segments

def save_html(segments, HTML_PATH):
    start = segments[0][1][0]
    karte = folium.Map(location=start, zoom_start=12)
    for color, coord in segments:
        folium.PolyLine(locations=coord,
                        color=color,
                        weight=3
        ).add_to(karte)

    karte.save(str(HTML_PATH))

def select_container():
    containers = fetch_containers(BASE_URL)["containers"]
    for i, container in enumerate(containers):
        print(f"{i+1}. {container}")
    while True:
        try:
            container_choice = int(input("Please enter Container Number "))
            container = containers[container_choice-1]
            break
        except ValueError:
            print("Invalid input. Please enter a valid number")
        except IndexError:
            print(f"Invalid choice. Please enter a number between 1 and {len(containers)}.")
    return container

def select_route(container_id):
    routes = fetch_routes(BASE_URL, container_id)["routes"]
    for i, route in enumerate(routes):
        print(f"{i+1}. {route}")
    while True:
        try:
            route_choice = int(input("Please enter Route Number "))
            route = routes[route_choice-1]
            break
        except ValueError:
            print("Invalid input. Please enter a valid number")
        except IndexError:
            print(f"Invalid choice. Please enter a number between 1 and {len(routes)}.")
    return route

def main():
    container_id = select_container()
    route_id = select_route(container_id)
    rows = fetch_csv(BASE_URL, container_id, route_id)
    segments = build_segments(rows)
    save_html(segments, HTML_PATH)
    webbrowser.open(str(HTML_PATH))

if __name__ == "__main__":
    main()