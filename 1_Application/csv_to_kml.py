from pathlib import Path
import csv
import simplekml
import webbrowser


def get_color(temp, humidity):
    if temp >= 25 and humidity >= 80:
        return simplekml.Color.red
    elif temp >= 25:
        return simplekml.Color.orange
    elif humidity >= 80:
        return simplekml.Color.yellow
    else:
        return simplekml.Color.blue

def build_segments(csv_path):
    segments = []
    current_color = None
    current_coords = []

    with open(csv_path, "r", newline="") as f:
        inputfile = csv.reader(f)

        for row in inputfile:
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

def save_kml(segments, output_path):
    kml = simplekml.Kml()

    for i, (color, coords) in enumerate(segments):
        line = kml.newlinestring(name=f"Route_{i}", coords=coords)
        line.style.linestyle.width = 3
        line.style.linestyle.color = color

    kml.save(str(output_path))

script_dir = Path(__file__).parent
csv_path = script_dir / "olten-brugg (2).csv"
output_path = script_dir / "olten-brugg.kml"

segments = build_segments(csv_path)
save_kml(segments, output_path)

webbrowser.open("https://kmlviewer.nsspot.net/")