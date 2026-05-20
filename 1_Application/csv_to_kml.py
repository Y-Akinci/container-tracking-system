from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils import build_segments
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


def save_kml(segments, KML_PATH):
    kml = simplekml.Kml()

    for i, (color, coords) in enumerate(segments):
        line = kml.newlinestring(name=f"Route_{i}", coords=coords)
        line.style.linestyle.width = 3
        line.style.linestyle.color = color

    kml.save(str(KML_PATH))

def main():
    rows = read_csv(CSV_PATH)
    segments = build_segments(rows, get_color)
    save_kml(segments, KML_PATH)
    webbrowser.open("https://kmlviewer.nsspot.net/")

if __name__ == "__main__":
    main()