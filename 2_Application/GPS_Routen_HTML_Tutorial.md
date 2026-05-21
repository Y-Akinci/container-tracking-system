# Python Tutorial: GPS-Routen interaktiv visualisieren mit Folium

In dieser zweiten Applikation erweitern wir das bestehende Container-Tracking-System. Statt GPS-Daten aus einer lokalen CSV-Datei einzulesen, werden die Daten nun von einem Webserver abgerufen. Zusätzlich kann der Benutzer im Terminal auswählen, welcher Container und welche Route angezeigt werden sollen. Die Route wird anschliessend als interaktive HTML-Karte im Browser visualisiert.

> ![alt text](image.png)

**Lerninhalt:**
1. Wie kommen Daten herein? — User Input im Terminal und Abruf von einem Webserver
2. Wie visualisiert man die Route? — Interaktive HTML-Karte mit Folium

---

## Voraussetzungen

Du kennst bereits folgende Konzepte aus App 1:

- Funktionen (`def`, `return`), Listen, `for`-Schleifen, `if/elif/else`
- `float()` für Typumwandlung aus CSV-Strings
- `pathlib` für Dateipfade
- Packages importieren, virtuelle Umgebung einrichten
- Die Logik von `get_color` und `build_segments` aus `utils.py`

Neu in diesem Tutorial:

- HTTP-Requests: wie man Daten von einem Server abruft
- JSON als Datenformat
- Fehlerbehandlung mit `try/except`
- Interaktive Karten mit `folium` als HTML-Datei

---

## Packages installieren

```bash
pip install requests folium
pip freeze > requirements.txt
```

`csv`, `io`, `pathlib`, `webbrowser` und `sys` sind in Python eingebaut — kein `pip` nötig.

---

## Konzepte

### HTTP und Webserver

Unsere Daten liegen nicht mehr als lokale CSV-Datei vor, sondern auf einem **Webserver**. Ein Webserver ist ein Programm das auf Anfragen wartet und Daten zurückschickt, genau wie ein Browser eine Webseite abruft, nur dass wir aus Python heraus fragen.

Das Protokoll dahinter heisst **HTTP** (HyperText Transfer Protocol). Es beschreibt, wie Anfragen und Antworten aussehen. Die einfachste Anfrage ist `GET`: "gib mir die Daten unter dieser Adresse":

```
GET https://mein-server.ch/containers
```

In Python macht das Paket `requests` genau das:

```python
response = requests.get("https://mein-server.ch/containers")
```

`response` enthält die Antwort des Servers — entweder als Text (`response.text`) oder direkt als Python-Objekt (`response.json()`), je nachdem was der Server zurückschickt.

Der Server stellt mehrere **Endpunkte** zur Verfügung. Das sind URLs, die verschiedene Daten zurückgeben:

```
GET /containers                                    → alle Container
GET /containers/{container_id}/routes              → alle Routen eines Containers
GET /containers/{container_id}/routes/{route_id}   → CSV-Daten einer Route
```

`{container_id}` und `{route_id}` sind Platzhalter — dort kommt der echte Wert rein, z.B. `frodo` oder `horw-luzern`.

---

### JSON

Die ersten zwei Endpunkte geben kein CSV zurück, sondern **JSON**. JSON ist ein Textformat das überall verwendet wird um strukturierte Daten zu übertragen. Es sieht aus wie Python, ist aber zunächst ein String:

```json
{"containers": ["frodo", "gimli", "grp1", "grp2"]}
```

`response.json()` wandelt diesen String automatisch in ein Python-Dictionary um:

```python
data = response.json()          # String -> Python Dictionary
containers = data["containers"] # Zugriff auf den Schlüssel
```

Der dritte Endpunkt gibt CSV-Text zurück. Dort verwenden wir `response.text`.

---

### HTML

Statt einer KML-Datei erzeugt Folium eine **HTML-Datei**. HTML (HyperText Markup Language) ist das Format, das Browser verstehen um Inhalte darzustellen, wie beispielsweise Webseiten, aber auch lokale Dateien. Folium schreibt die Karte inklusive JavaScript in eine einzelne `.html`-Datei, die sich direkt im Browser öffnen lässt. Das Prinzip ist dasselbe wie bei KML: wir erzeugen eine Datei, ein Viewer zeigt sie an — nur dass der Viewer hier der Browser ist.

---

### Fehlerbehandlung mit try/except

Wenn der Benutzer eine ungültige Eingabe macht, z.B. einen Buchstaben statt einer Zahl, oder eine Zahl ausserhalb der Liste, würde Python normalerweise mit einem Fehler abbrechen. Mit `try/except` fangen wir diese Fehler ab und können darauf reagieren:

```python
try:
    zahl = int(input("Zahl eingeben: "))
    wert = liste[zahl - 1]
except ValueError:
    print("Das war keine Zahl.")
except IndexError:
    print("Diese Nummer existiert nicht.")
```

**`ValueError`** tritt auf wenn `int()` einen String bekommt den es nicht umwandeln kann, z.B. `"abc"`.

**`IndexError`** tritt auf wenn der Index ausserhalb der Liste liegt, z.B. `99` bei 4 Einträgen.

Wichtig: alles was einen Fehler auslösen kann muss **innerhalb** von `try` stehen. Der Zugriff auf die Liste (`liste[zahl - 1]`) muss also im selben `try`-Block sein wie `int()`, sonst greift `except IndexError` nicht.

---

## Schritt 1: Packages und Pfade einrichten

```python
import requests
import io
import csv
import folium
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import build_segments
import webbrowser

BASE_URL = "https://fl-17-240.zhdk.cloud.switch.ch"
SCRIPT_DIR = Path(__file__).parent
HTML_PATH = SCRIPT_DIR / "karte.html"
```

`BASE_URL` ist die Adresse des Servers. Alle Endpunkte werden mit f-Strings daran angehängt.

---

## Schritt 2: Daten vom Server abrufen

```python
def fetch_containers(BASE_URL):
    response = requests.get(BASE_URL + "/containers")
    return response.json()

def fetch_routes(BASE_URL, container_id):
    response = requests.get(BASE_URL + f"/containers/{container_id}/routes")
    return response.json()

def fetch_csv(BASE_URL, container_id, route_id):
    response = requests.get(BASE_URL + f"/containers/{container_id}/routes/{route_id}")
    rows = list(csv.reader(io.StringIO(response.text)))
    return rows
```

Die ersten zwei Funktionen geben JSON zurück — `response.json()` liefert direkt ein Dictionary. Die dritte gibt CSV-Text zurück — dort verwenden wir `response.text`.

`io.StringIO` macht aus dem CSV-String eine virtuelle Datei, die `csv.reader` genau gleich lesen kann wie eine echte Datei:

```python
# App 1: echte Datei von der Festplatte
with open(csv_path) as f:
    rows = list(csv.reader(f))

# App 2: String vom Server
rows = list(csv.reader(io.StringIO(response.text)))
```

Das Ergebnis — `rows` — ist in beiden Fällen identisch.

---

## Schritt 3: Farbe pro Messpunkt bestimmen

```python
def get_color(temp, humidity):
    if temp >= 25 and humidity >= 80:
        return "red"
    elif temp >= 25:
        return "orange"
    elif humidity >= 80:
        return "yellow"
    else:
        return "blue"
```

Die Logik ist identisch zu App 1. Der einzige Unterschied: statt `simplekml.Color.red` verwenden wir einfache Farb-Strings, die Folium versteht. `build_segments` aus `utils.py` bleibt komplett unverändert.

---

## Schritt 4: Benutzer wählt Container und Route

```python
def select_container():
    containers = fetch_containers(BASE_URL)["containers"]
    for i, container in enumerate(containers):
        print(f"{i+1}. {container}")
    while True:
        try:
            container_choice = int(input("Please enter Container Number "))
            if container_choice < 1:
                print(f"Invalid choice. Please enter a number between 1 and {len(containers)}.")
                continue
            container = containers[container_choice - 1]
            break
        except ValueError:
            print("Invalid input. Please enter a valid number")
        except IndexError:
            print(f"Invalid choice. Please enter a number between 1 and {len(containers)}.")
    return container
```

`while True` läuft so lange bis der Benutzer eine gültige Eingabe macht. `break` beendet die Schleife sobald alles erfolgreich war. `continue` springt direkt zum nächsten Schleifendurchlauf — damit wird eine negative Zahl abgefangen, bevor sie als Index verwendet wird.

`containers[container_choice - 1]` steht innerhalb von `try`, damit `IndexError` abgefangen wird. `-1` weil der Benutzer ab 1 zählt, Python ab 0.

`select_route` funktioniert identisch, nur mit Routen statt Containern.

```python
def select_route(container_id):
    routes = fetch_routes(BASE_URL, container_id)["routes"]
    for i, route in enumerate(routes):
        print(f"{i+1}. {route}")
    while True:
        try:
            route_choice = int(input("Please enter Route Number "))
            if route_choice < 1:
                print(f"Invalid choice. Please enter a number between 1 and {len(routes)}.")
                continue
            route = routes[route_choice-1]
            break
        except ValueError:
            print("Invalid input. Please enter a valid number")
        except IndexError:
            print(f"Invalid choice. Please enter a number between 1 and {len(routes)}.")
    return route
```

---

## Schritt 5: Interaktive Karte erstellen

```python
def save_html(segments, HTML_PATH):
    start = segments[0][1][0]
    karte = folium.Map(location=start, zoom_start=12)
    for color, coord in segments:
        folium.PolyLine(
            locations=coord,
            color=color,
            weight=3
        ).add_to(karte)
    karte.save(str(HTML_PATH))
```

**`segments[0][1][0]`** greift auf die erste Koordinate der Route zu — sie dient als Startpunkt der Karte:

```python
segments[0]       # erstes Segment -> ("blue", [(lat1,lon1), (lat2,lon2)])
segments[0][1]    # Koordinatenliste -> [(lat1,lon1), (lat2,lon2)]
segments[0][1][0] # erste Koordinate -> (lat1, lon1)
```

**`folium.Map()`** erstellt die Karte. **`folium.PolyLine()`** zeichnet eine Linie pro Segment. **`.add_to(karte)`** fügt sie zur Karte hinzu. **`karte.save()`** schreibt die fertige Karte als HTML-Datei.

Folium erwartet Koordinaten als `(latitude, longitude)` — das ist dieselbe Reihenfolge wie in `build_segments` in `utils.py`.

---

## Schritt 6: Alles zusammensetzen

```python
def main():
    container_id = select_container()
    route_id = select_route(container_id)
    rows = fetch_csv(BASE_URL, container_id, route_id)
    segments = build_segments(rows, get_color)
    save_html(segments, HTML_PATH)
    webbrowser.open(str(HTML_PATH))

if __name__ == "__main__":
    main()
```

`main()` beschreibt nur den Ablauf auf hoher Ebene. Jeder Schritt ist sofort lesbar ohne die Details zu kennen. `webbrowser.open` öffnet die fertige HTML-Datei direkt im Browser.

---

## Klassische Fehler

**`IndexError` nicht abgefangen:** Wenn `containers[choice - 1]` ausserhalb von `try` steht, greift `except IndexError` nicht, auch wenn es vorhanden ist. Der Zugriff auf die Liste muss innerhalb von `try` stehen.

**`response.json()` statt `response.text`:** Bei den ersten zwei Endpunkten kommt JSON zurück ->`response.json()` verwenden. Bei der CSV kommt Text zurück -> `response.text` verwenden. Verwechslung führt zu einem Fehler.

**Dictionary-Schlüssel vergessen:** `response.json()` gibt ein Dictionary zurück, keine Liste. Ohne `["containers"]` bekommst du das ganze Dictionary statt der Liste der Container.

**Koordinatenreihenfolge:** Folium erwartet `(latitude, longitude)`. KML in App 1 erwartete `(longitude, latitude)`. `build_segments` in `utils.py` gibt `(latitude, longitude)` zurück — passt also direkt zu Folium.
