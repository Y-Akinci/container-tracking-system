from pathlib import Path
import csv
import simplekml
import webbrowser

SCRIPT_DIR = Path(__file__).parent
CSV_PATH = SCRIPT_DIR / "olten-brugg (2).csv"
KML_PATH = SCRIPT_DIR / "olten-brugg.kml"

def read_csv(CSV_PATH):
    with open(CSV_PATH, "r", newline="") as f:
        inputfile = csv.reader(f)
        rows = list(inputfile)
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

def save_kml(segments, KML_PATH):
    kml = simplekml.Kml()

    for i, (color, coords) in enumerate(segments):
        line = kml.newlinestring(name=f"Route_{i}", coords=coords)
        line.style.linestyle.width = 3
        line.style.linestyle.color = color

    kml.save(str(KML_PATH))

def main():
    rows = read_csv(CSV_PATH)
    segments = build_segments(rows)
    save_kml(segments, KML_PATH)
    webbrowser.open("https://kmlviewer.nsspot.net/")

if __name__ == "__main__":
    main()