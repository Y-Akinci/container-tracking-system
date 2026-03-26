from pathlib import Path
import csv
import simplekml
import webbrowser

script_dir = Path(__file__).parent
csv_path = script_dir / "olten-brugg (2).csv"

kml = simplekml.Kml()
inputfile = csv.reader(open(csv_path, "r"))

segments = [] # Eine Liste welche die Teile der strecke mit den Farben Enthält, komplett
current_color = None # Damit momentane farbe nichts ist, für den farbwechsel
current_coords = [] # Es gruppiert die farben zusammen, im aufbau

for row in inputfile:# Werte muss in float umgewandelt werden, weil csv als string liest
    if float(row[3]) >= 25 and float(row[4]) >= 80: 
        color = simplekml.Color.red
    elif float(row[3]) >= 25:
        color = simplekml.Color.orange
    elif float(row[4]) >= 80:
        color = simplekml.Color.yellow
    else:
        color = simplekml.Color.blue

    if color != current_color: # Hat sich die Farbe im Vergleich zur vorherigen Zeile geändert?
        if current_coords:
            segments.append((current_color, current_coords))
            current_coords = [current_coords[-1]]
        current_color = color

    current_coords.append((float(row[2]), float(row[1])))

segments.append((current_color, current_coords))

for i, (color, coords) in enumerate(segments):
    line = kml.newlinestring(name=f"Route_{i}", coords=coords)
    line.style.linestyle.width = 3
    line.style.linestyle.color = color

kml.save(str(script_dir / "olten-brugg.kml"))

print(row[0], row[1], row[2])

webbrowser.open("https://kmlviewer.nsspot.net/")