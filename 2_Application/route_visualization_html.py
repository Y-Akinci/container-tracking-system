import requests
import io
import csv
import folium
import sys
from pathlib import Path

# Zugriff auf utils.py im übergeordneten Projektordner ermöglichen
sys.path.append(str(Path(__file__).parent.parent))

from utils import build_segments
import webbrowser

BASE_URL = "https://fl-17-240.zhdk.cloud.switch.ch"
SCRIPT_DIR = Path(__file__).parent
HTML_PATH = SCRIPT_DIR / "karte.html"

# Container vom Webserver abrufen
def fetch_containers(BASE_URL):
    response = requests.get(BASE_URL + "/containers")
    return response.json()

# Routen eines Containers vom Webserver abrufen
def fetch_routes(BASE_URL, container_id):
    response = requests.get(BASE_URL + f"/containers/{container_id}/routes")
    return response.json()

# CSV-Daten einer Route vom Webserver abrufen und einlesen
def fetch_csv(BASE_URL, container_id, route_id):
    response = requests.get(BASE_URL + f"/containers/{container_id}/routes/{route_id}")
    rows = list(csv.reader(io.StringIO(response.text)))
    return rows

# Farbe anhand von Temperatur und Luftfeuchtigkeit bestimmen
def get_color(temp, humidity):
    if temp >= 25 and humidity >= 80:
        return "red"
    elif temp >= 25:
        return "orange"
    elif humidity >= 80:
        return "yellow"
    else:
        return "blue"

# Route als HTML-Karte speichern
def save_html(segments, HTML_PATH):
    start = segments[0][1][0]
    karte = folium.Map(location=start, zoom_start=12)
    for color, coord in segments:
        folium.PolyLine(locations=coord,
                        color=color,
                        weight=3
        ).add_to(karte)

    karte.save(str(HTML_PATH))

# Benutzer wählt einen Container aus
def select_container():
    containers = fetch_containers(BASE_URL)["containers"]
    for i, container in enumerate(containers):
        print(f"{i+1}. {container}")
    while True:
        try:
            container_choice = int(input("Please enter Container Number "))
            if container_choice < 1:
                print(f"Invalid choice. Please enter a number between 1 and {len(containers)}.")
                continue
            container = containers[container_choice-1]
            break
        except ValueError:
            print("Invalid input. Please enter a valid number")
        except IndexError:
            print(f"Invalid choice. Please enter a number between 1 and {len(containers)}.")
    return container

# Benutzer wählt eine Route des Containers aus
def select_route(container_id):
    routes = fetch_routes(BASE_URL, container_id)["routes"]
    for i, route in enumerate(routes):
        print(f"{i+1}. {route}")
    while True:
        try:
            route_choice = int(input("Please enter Route Number "))
            if route_choice < 1:
                print(f"Invalid choice. Please enter a number between 1 and {len(routes)}.")
                continue
            route = routes[route_choice-1]
            break
        except ValueError:
            print("Invalid input. Please enter a valid number")
        except IndexError:
            print(f"Invalid choice. Please enter a number between 1 and {len(routes)}.")
    return route

# Hauptablauf des Programms
def main():
    container_id = select_container()
    route_id = select_route(container_id)
    rows = fetch_csv(BASE_URL, container_id, route_id)
    segments = build_segments(rows, get_color)
    save_html(segments, HTML_PATH)
    webbrowser.open(str(HTML_PATH))

# Programm nur starten, wenn diese Datei direkt ausgeführt wird
if __name__ == "__main__":
    main()