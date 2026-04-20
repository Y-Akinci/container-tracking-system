from pathlib import Path
import csv
import folium
import webbrowser

script_dir = Path(__file__).parent
csv_path = script_dir / "olten-brugg (2).csv"

inputfile = list(csv.reader(open(csv_path, "r")))

map = folium.Map(location=[float(inputfile[0][1]), float(inputfile[0][2])], zoom_start=13)

segments = []
current_color = None
current_coords = []

for row in inputfile:
    if float(row[3]) >= 25 and float(row[4]) >= 80:
        color = "red"
    elif float(row[3]) >= 25:
        color = "orange"
    elif float(row[4]) >= 80:
        color = "yellow"
    else:
        color = "blue"

    if color != current_color:
        if current_coords:
            segments.append((current_color, current_coords))
            current_coords = [current_coords[-1]]
        current_color = color

    current_coords.append((float(row[1]), float(row[2])))

segments.append((current_color, current_coords))

for color, coords in segments:
    folium.PolyLine(coords, color=color, weight=4).add_to(map)

map_path = script_dir / "olten-brugg.html"
map.save(str(map_path))

webbrowser.open(str(map_path))