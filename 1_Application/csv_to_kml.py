from pathlib import Path
import csv
import simplekml

# Zugriff auf die CSV-Datei im selben Verzeichnis wie das Skript
script_dir = Path(__file__).parent
csv_path = script_dir / "olten-brugg (2).csv"

# Erstellen eines KML-Objekts
kml = simplekml.Kml()


inputfile = csv.reader(open(csv_path, "r"))
for row in inputfile:
    pnt = kml.newpoint(coords=[(row[2], row[1])])
    pnt.description = f"DateTime: {row[0]}, Temperatur: {row[3]}, Luftfeuchtigkeit: {row[4]}, "
    if float(row[3]) >= 25:
        pnt.style.iconstyle.color = simplekml.Color.orange
    elif float(row[3]) >= 25 and float(row[4]) >= 75:
        pnt.style.iconstyle.color = simplekml.Color.orange
    else:
        pnt.style.iconstyle.color = simplekml.Color.blue

kml.save(str(script_dir / "olten-brugg.kml"))

print(row[0], row[1], row[2])
