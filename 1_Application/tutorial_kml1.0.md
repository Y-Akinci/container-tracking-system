# Python Tutorial: GPS-Routen visualisieren mit KML

Wir haben im Modul CDE1 ein Container-Tracking-System gebaut. GPS-Daten kommen als CSV-Datei an, wir lesen sie aus, bewerten Temperatur und Feuchtigkeit, und zeichnen die Route farbig auf einer Karte. Dieses Tutorial erklärt nicht nur was wir gemacht haben, sondern vor allem warum und wie du es selbst nachbauen kannst.

## Voraussetzungen

Du solltest bereits wissen was das bedeutet:

```python
if temp >= 25:
    print("zu warm")
elif temp >= 20:
    print("okay")
else:
    print("kalt")

for row in data:
    print(row)
```

## Schritt 1: Virtuelle Umgebung mit venv

Wenn du einfach `pip install simplekml` ausführst, wird das Paket **global** installiert, also für den ganzen Computer. Das klingt praktisch, führt aber zu Problemen sobald du mehrere Projekte hast die verschiedene Versionen desselben Pakets brauchen. Python kann nicht zwei Versionen gleichzeitig global installiert haben.

Die Lösung ist eine **virtuelle Umgebung**. Das ist ein isolierter Python-Bereich nur für dein Projekt. Jedes Projekt hat seine eigenen Pakete in eigenen Versionen, kein Konflikt, kein Chaos.

### Virtuelle Umgebung erstellen und aktivieren

```bash
# Im Projektordner: virtuelle Umgebung erstellen
python -m venv .venv

# Aktivieren auf Windows (PowerShell)
.\.venv\Scripts\Activate

# Aktivieren auf Mac / Linux
source .venv/bin/activate
```

Du merkst dass die venv aktiv ist wenn `(.venv)` vor deiner Eingabe erscheint:

```
(.venv) PS C:\mein-projekt>
```

### Pakete installieren und festhalten

```bash
# Paket installieren (nur in der venv, nicht global)
pip install simplekml

# Alle installierten Pakete in eine Datei schreiben
pip freeze > requirements.txt
```

Die `requirements.txt` sieht dann zum Beispiel so aus:

```
simplekml==1.3.6
```

Wer dein Projekt bekommt, kann mit einem einzigen Befehl exakt dieselbe Umgebung wiederherstellen:

```bash
pip install -r requirements.txt
```

Den Ordner `.venv` teilt man nicht, er kann aus `requirements.txt` jederzeit neu erstellt werden. Füge `.venv` in deine `.gitignore` ein wenn du Git verwendest.

## Schritt 2: Packages, was sie sind und wie man sie benutzt

Ein **Package** ist fertiger Code den andere geschrieben haben und den du in deinem Projekt verwenden kannst. Statt alles selbst zu programmieren, nutzt du was bereits existiert.

### Wie man ein Package einbindet

Oben in jeder Python-Datei stehen die `import`-Zeilen. Sie laden den Code des Packages in dein Script:

```python
from pathlib import Path  # eingebaut in Python, kein pip nötig
import csv                # eingebaut in Python
import simplekml          # muss installiert werden: pip install simplekml
import webbrowser         # eingebaut in Python
```

Der Unterschied zwischen `import paket` und `from paket import teil`:

```python
import simplekml
# Zugriff immer mit Paketname: simplekml.Kml(), simplekml.Color.red

from pathlib import Path
# Direkter Zugriff: Path(...), kürzer weil wir nur Path brauchen
```

### Welche Packages wir verwenden und warum

**`csv`** ist bereits in Python eingebaut, kein `pip install` nötig. Wir hätten auch `pandas` verwenden können, aber `pandas` ist ein grosses, komplexes Paket das für unseren Fall überdimensioniert wäre. Wir lesen eine Datei linear durch, dafür reicht `csv` vollständig.

**`pathlib`** löst ein klassisches Problem mit Dateipfaden. Früher schrieb man Pfade als einfache Strings:

```python
# Alt, funktioniert nur auf diesem einen Computer
pfad = "C:\\Users\\User\\projekt\\daten.csv"
```

Mit `pathlib` geht das so:

```python
# Modern, funktioniert überall egal von wo man das Script startet
script_dir = Path(__file__).parent
pfad = script_dir / "daten.csv"
```

`__file__` ist eine eingebaute Variable die den absoluten Pfad der aktuellen Python-Datei enthält. `.parent` gibt den Ordner zurück in dem sie liegt. Der `/`-Operator bei `Path`-Objekten baut Pfade plattformunabhängig zusammen, kein Unterschied mehr zwischen Windows und Mac/Linux.

**`simplekml`** erzeugt KML-Dateien. KML ist ein XML-Format das Google Maps und viele andere Viewer verstehen. Wir hätten die KML-Datei von Hand als Text schreiben können, aber das wäre fehleranfällig und aufwändig. `simplekml` abstrahiert das weg.

**`webbrowser`** ist in Python eingebaut und öffnet eine URL im Standardbrowser des Computers. Damit sehen wir das Resultat direkt nach dem Ausführen, ohne manuell in den Browser wechseln zu müssen.

## Schritt 3: Die CSV-Datei verstehen

Bevor wir Code schreiben, müssen wir wissen wie unsere Daten aussehen. Unsere CSV hat keine Header-Zeile, die Daten beginnen direkt in Zeile 1:

```
2024-03-15 08:00:00,47.3523,7.9072,22.1,65.3
2024-03-15 08:00:10,47.3541,7.9089,24.8,72.1
2024-03-15 08:00:20,47.3558,7.9103,26.3,81.5
```

Das ergibt folgende Spalten-Indizes:

```python
row[0]  # Zeitstempel  -> "2024-03-15 08:00:00"
row[1]  # Latitude     -> "47.3523"
row[2]  # Longitude    -> "7.9072"
row[3]  # Temperatur   -> "22.1"
row[4]  # Feuchtigkeit -> "65.3"
```

`csv.reader` liest alles als **String**, auch Zahlen. `"22.1"` ist kein Zahlenwert, man kann damit nicht rechnen oder vergleichen. Deshalb müssen wir `float(row[3])` schreiben um den String in eine Dezimalzahl umzuwandeln.

### CSV öffnen mit `with open(...)`

```python
with open(csv_path, "r", newline="") as f:
    inputfile = csv.reader(f)
    rows = list(inputfile)
    return rows #['2024-03-15 08:00:00', '47.3523', '7.9072', '22.1', '65.3']
```

Das `with`-Statement stellt sicher dass die Datei automatisch geschlossen wird, auch wenn ein Fehler passiert. Das ist sicherer als manuell `f.close()` aufzurufen.

`newline=""` verhindert dass Python Zeilenumbrüche doppelt interpretiert. Das ist eine Empfehlung der offiziellen Python-Dokumentation für `csv.reader`.



## Schritt 4: simplekml, wie man eine Kartenroute erstellt

### Das KML-Objekt erstellen

Alles beginnt mit einem `Kml()`-Objekt. Es ist der Container für alles was wir in die Datei schreiben wollen:

```python
import simplekml

kml = simplekml.Kml()
```

### Eine Linie zeichnen

Eine Linie in KML heisst `LineString`. Mit `simplekml` erstellt man sie so:

```python
koordinaten = [
    (7.9072, 47.3523),  # (longitude, latitude), Reihenfolge beachten!
    (7.9089, 47.3541),
    (7.9103, 47.3558),
]

linie = kml.newlinestring(name="Meine Route", coords=koordinaten)
```

Achtung: KML erwartet die Koordinaten in der Reihenfolge **(longitude, latitude)**, also Längengrad zuerst, Breitengrad zweiter. Das ist das Gegenteil von dem was man intuitiv erwartet. Dieser Fehler ist uns beim ersten Versuch passiert, die Route war plötzlich irgendwo im Atlantik.

### Farbe und Breite der Linie setzen

```python
linie.style.linestyle.width = 3
linie.style.linestyle.color = simplekml.Color.red
```

Verfügbare Farben in `simplekml`:

```python
simplekml.Color.red
simplekml.Color.orange
simplekml.Color.yellow
simplekml.Color.blue
simplekml.Color.green
simplekml.Color.white
simplekml.Color.black
```

### Die Datei speichern

```python
kml.save("olten-brugg.kml")
```

Mit `pathlib` damit die Datei immer im richtigen Ordner landet:

```python
script_dir = Path(__file__).parent
kml.save(str(script_dir / "olten-brugg.kml"))
```

`kml.save()` erwartet einen String, deshalb `str(...)` um das `Path`-Objekt umzuwandeln.

### Zeitstempel auf Punkte setzen (Bonus)

KML unterstützt Zeitstempel auf einzelnen Punkten. Das erlaubt es Viewern wie Google Earth, die Route als **Animation** abzuspielen. Man sieht wie der Container sich über die Zeit bewegt.

```python
punkt = kml.newpoint(name="Checkpoint", coords=[(7.9072, 47.3523)])
punkt.timestamp.when = "2024-03-15T08:00:00"
```

Das Format muss ISO 8601 sein: `YYYY-MM-DDTHH:MM:SS`. Unsere CSV hat ein Leerzeichen zwischen Datum und Uhrzeit statt dem `T`, das lässt sich einfach korrigieren:

```python
raw = row[0]                 # "2024-03-15 08:00:00"
iso = raw.replace(" ", "T")  # "2024-03-15T08:00:00"
```

Ein vollständiges Beispiel das für jeden GPS-Punkt einen Zeitstempel-Marker setzt:

```python
from pathlib import Path
import csv
import simplekml

kml = simplekml.Kml()
script_dir = Path(__file__).parent

with open(script_dir / "olten-brugg (2).csv", "r", newline="") as f:
    for row in csv.reader(f):
        lon      = float(row[2])
        lat      = float(row[1])
        iso_time = row[0].replace(" ", "T")

        punkt = kml.newpoint(coords=[(lon, lat)])
        punkt.timestamp.when = iso_time

kml.save(str(script_dir / "route_mit_zeit.kml"))
```

## Schritt 5: Farbige Segmente, das Herzstück

### Warum Segmente und nicht einzelne Punkte?

Der naive Ansatz wäre, jeden GPS-Punkt als eigene Linie zu zeichnen. Das erzeugt hunderte kleine Einzellinien und ist ineffizient. Unser Ansatz: Solange aufeinanderfolgende Punkte dieselbe Farbe haben, sammeln wir sie in einem Segment. Erst wenn die Farbe wechselt, beginnt ein neues Segment.

### Farbe bestimmen mit get_color()

```python
def get_color(temp, humidity):
    if temp >= 25 and humidity >= 80:
        return simplekml.Color.red     # zu warm UND zu feucht
    elif temp >= 25:
        return simplekml.Color.orange  # nur zu warm
    elif humidity >= 80:
        return simplekml.Color.yellow  # nur zu feucht
    else:
        return simplekml.Color.blue    # alles normal
```

Das `and` in der ersten Bedingung ist entscheidend: Nur wenn beide Kriterien zutreffen, wird es Rot. `elif` stellt sicher dass immer genau eine Farbe gewählt wird. Die erste zutreffende Bedingung gewinnt, der Rest wird übersprungen.

Wir haben diese Logik in eine eigene Funktion ausgelagert damit wir sie isoliert testen können. `get_color(30, 90)` sollte Rot zurückgeben. Das macht die Hauptlogik ausserdem übersichtlicher.

### Segmente aufbauen mit build_segments()

```python
def build_segments(rowa):
    segments = []        # fertige Segmente: [(farbe, [koordinaten]), ...]
    current_color = None # aktuelle Farbe, zu Beginn noch keine
    current_coords = []  # Koordinaten des aktuellen Segments


    for row in rows:
        temp     = float(row[3])
        humidity = float(row[4])
        color    = get_color(temp, humidity)
        coord    = (float(row[2]), float(row[1]))  # (longitude, latitude)

        if color != current_color:          # Farbwechsel erkannt
            if current_coords:              # Haben wir schon Punkte gesammelt?
                segments.append((current_color, current_coords))
                current_coords = [current_coords[-1]]  # letzten Punkt übernehmen
            current_color = color

        current_coords.append(coord)

    if current_coords:                          # letztes Segment nicht vergessen
        segments.append((current_color, current_coords))

    return segments
```

**Warum `current_coords[-1]`?**
Wenn ein Segment endet und ein neues beginnt, übernehmen wir den letzten Punkt des alten Segments als ersten Punkt des neuen. Ohne das hätte die Route sichtbare Lücken an jedem Farbwechsel. `[-1]` ist der Python-Index für das letzte Element einer Liste.

**Warum nochmals `append` nach der Schleife?**
Die Schleife speichert ein Segment erst wenn die Farbe wechselt. Das allerletzte Segment wird nie durch einen Wechsel abgeschlossen, ohne die Zeile nach der Schleife würde das Ende der Route in der KML-Datei fehlen, ohne jede Fehlermeldung.

### Segmente in KML schreiben mit save_kml()

```python
def save_kml(segments, kml_path):
    kml = simplekml.Kml()

    for i, (color, coords) in enumerate(segments):
        line = kml.newlinestring(name=f"Route_{i}", coords=coords)
        line.style.linestyle.width = 3
        line.style.linestyle.color = color

    kml.save(str(kml_path))
```

`enumerate(segments)` gibt uns gleichzeitig den Index `i` und den Wert `(color, coords)`, so können wir jede Linie eindeutig benennen (`Route_0`, `Route_1`, ...).

Wir haben das Speichern in eine eigene Funktion ausgelagert damit `build_segments()` nichts davon wissen muss, dass am Ende eine KML-Datei entsteht. Die Trennung macht den Code austauschbar: willst du statt KML ein anderes Format, schreibst du einfach eine neue `save_`-Funktion und der Rest bleibt unverändert.

## Schritt 6: Alles zusammensetzen

Der vollständige, lauffähige Code:

```python
from pathlib import Path
import csv
import simplekml
import webbrowser

script_dir  = Path(__file__).parent
csv_path    = script_dir / "olten-brugg (2).csv"
output_path = script_dir / "olten-brugg.kml"

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
        temp     = float(row[3])
        humidity = float(row[4])
        color    = get_color(temp, humidity)
        coord    = (float(row[2]), float(row[1]))

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

def main():
    rows = read_csv(csv_path)
    segments = build_segments(rows)
    save_kml(segments, output_path)
    webbrowser.open("https://kmlviewer.nsspot.net/")

if __name__ == "__main__":
    main()
```

**Warum steht der ausführende Code am Ende?**
In Python wird Code von oben nach unten gelesen. Würden wir `build_segments()` aufrufen bevor die Funktion definiert ist, stürzt Python ab. Deshalb erst alle Funktionen definieren, dann aufrufen.

## Klassische Fehler aus unserer eigenen Erfahrung

**Falscher Spalten-Index:** Unsere CSV hat keine Header-Zeile. Wenn du den falschen Index verwendest bekommst du falsche Werte ohne Fehlermeldung. Python stürzt nicht ab, du bekommst einfach falsche Farben auf der Karte. Immer zuerst die CSV-Struktur prüfen bevor du Indizes verwendest.

**Letztes Segment vergessen:** Die Schleife endet, aber das letzte Segment wurde noch nicht gespeichert. Ohne `if current_coords: segments.append(...)` nach der Schleife fehlt das Ende der Route, ohne jede Fehlermeldung.

**Koordinaten falsch herum:** KML erwartet `(longitude, latitude)`, nicht `(latitude, longitude)`. Das ist verwirrend aber ein Standard den wir nicht ändern können. Beim ersten Versuch war unsere Route irgendwo im Atlantik.

**float() vergessen:** `csv.reader` liest alles als String. `"22.1" >= 25` vergleicht einen String mit einer Zahl, das ergibt in Python einen `TypeError`. Immer `float()` verwenden bevor du mit CSV-Werten rechnest oder vergleichst.
