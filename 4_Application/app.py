from flask import Flask
from database import get_routes, get_route_points
import sys
from pathlib import Path

# Zugriff auf utils.py im übergeordneten Projektordner ermöglichen
sys.path.append(str(Path(__file__).parent.parent))

from utils import build_segments
import folium

# Flask-App erstellen
app = Flask(__name__)

# Farbe eines Streckenabschnitts bestimmen
def get_color(temp, humidity):
    if temp >= 25 and humidity >= 80:
        return "red"
    elif temp >= 25:
        return "orange"
    elif humidity >= 80:
        return "yellow"
    else:
        return "blue"

# Funktion aufrufen, wenn Startseite "/" im Browser geöffent wird
@app.route("/")
def index():

    # lädt alles Routen aus der Datenbank
    routes = get_routes()

    html = "<h1>Container Dashboard</h1><ul>"
    for row in routes:
        container = row[1]
        route = row[2]
        start = row[3]
        end = row[4]
        problem = row[5]
        status = '<span style="color:red">Temperaturproblem</span>' if problem else '<span style="color:green">OK</span>'
        
        # Fügt einen Listeneintrag zur HTML-Seite hinzu.
        html += f'<li><a href="/route/{container}/{route}">{container} – {route}</a> | {start} bis {end} | {status}</li>'
    
    html += "</ul>"
    return html

# Funktion aufgerufen, wenn Route im Browser geöffnet
@app.route("/route/<container>/<route>")
def show_route(container, route):
    rows = get_route_points(container, route)
    if not rows:
        return "<h1>Keine Daten gefunden</h1>"
    
    # Teilt Route in farbige Streckenabschnitte ein
    segments = build_segments(rows, get_color)

    start = segments[0][1][0]
    karte = folium.Map(location=start, zoom_start=12)
    for color, coords in segments:
        folium.PolyLine(locations=coords, color=color, weight=3).add_to(karte)

    # Gibt die Folium-Karte als HTML zurück, damit sie im Browser angezeigt wird.
    return karte._repr_html_()

if __name__ == "__main__":
    app.run(debug=True)