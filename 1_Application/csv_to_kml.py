from pathlib import Path
import csv
from matplotlib import colors
import simplekml

# Zugriff auf die CSV-Datei im selben Verzeichnis wie das Skript
script_dir = Path(__file__).parent
csv_path = script_dir / "olten-brugg (2).csv"

# Erstellen eines KML-Objekts
kml = simplekml.Kml()
inputfile = csv.reader(open(csv_path, "r"))

segments = []
current_color = None
current_coords = []

for row in inputfile:
    if float(row[3]) >= 25 and float(row[4]) >= 80:
        color = simplekml.Color.red
    elif float(row[3]) >= 25:
        color = simplekml.Color.orange
    elif float(row[4]) >= 80:
        color = simplekml.Color.yellow
    else:
        color = simplekml.Color.blue

    if color != current_color:
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
