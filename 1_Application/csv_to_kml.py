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
    kml.newpoint(name="olten_brugg", coords=[(row[1], row[2])])

kml.save(str(script_dir / "olten-brugg.kml"))

    