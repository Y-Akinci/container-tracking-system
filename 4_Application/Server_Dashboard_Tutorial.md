# Python Tutorial: Eigener Server mit Datenbank und Dashboard

In dieser vierten und letzten Applikation drehen wir das ganze Prinzip um. In
App 1 bis 3 haben wir Daten **konsumiert**: aus einer CSV-Datei, von einem
fremden Webserver, über MQTT. Jetzt bauen wir die andere Seite. App 4 empfängt
die Live-Daten des Simulators, speichert sie dauerhaft in einer Datenbank und
zeigt sie über unseren **eigenen** Webserver als Dashboard im Browser an.

> ![alt text](image.png)

**Lerninhalt:**
1. Wie speichert man laufend eintreffende Daten dauerhaft? Datenbank mit SQLite
2. Wie stellt man eigene Daten im Browser bereit? Eigener Webserver mit Flask

---

## Voraussetzungen

Du kennst bereits folgende Konzepte aus App 1 bis 3:

- Funktionen (`def`, `return`), Listen, Dictionaries, `for`-Schleifen, `if/elif/else`
- `float()` für Typumwandlung
- `pathlib` für Dateipfade, Packages importieren, virtuelle Umgebung einrichten
- Die Logik von `get_color` und `build_segments` aus `utils.py`
- MQTT mit `paho-mqtt`, Callbacks `on_connect` und `on_message`
- JSON als Datenformat (`json.loads`)
- Interaktive Karten mit `folium`

Ausserdem brauchst du den **Simulator aus App 3** (`simulator.py`) samt seiner
Config `config-switch-grp4.ini` und einer Routendatei wie
`data/olten-brugg.geojson`. Der Simulator sendet die GPS-Punkte über MQTT, und
genau denen hört `ingest.py` zu. App 4 baut nur die Empfänger- und Anzeigeseite;
gesendet wird weiterhin wie in App 3.

Neu in diesem Tutorial:

- Daten dauerhaft speichern mit einer Datenbank (SQLite, eingebaut in Python)
- Ein bisschen SQL: ein paar Sätze reichen
- Einen eigenen Webserver bauen mit `flask`
- Zwei Endlosschleifen gleichzeitig laufen lassen mit einem Thread (`threading`)
- Der Perspektivwechsel: in App 2 waren wir der Client, jetzt sind wir der Server

---

## Packages installieren

```bash
pip install flask paho-mqtt folium
pip freeze > requirements.txt
```

`sqlite3` und `json` sind in Python eingebaut, kein `pip` nötig, genau wie
`csv` in App 1.

---

## Konzepte

### Die Idee: Sammeln und Anzeigen trennen

App 4 ist auf drei Dateien aufgeteilt, jede mit genau einer Aufgabe. Sie teilen
sich eine Datenbank und kennen einander sonst kaum:

```
[Simulator] --MQTT--> [ingest.py] --speichert--> [tracking.db] <--liest-- [app.py] --> [Browser]
```

- **`database.py`** ist die Datenschicht: sie legt die Datenbank an (`init_db`) und stellt
  Funktionen zum Speichern (`save_message`) und Lesen (`get_routes`,
  `get_route_points`) bereit. Sie kennt weder MQTT noch Flask, nur SQLite.
- **`ingest.py`** ist der Sammler: er hört dem Broker zu und schreibt jeden
  empfangenen Punkt über `save_message` in die Datenbank. Er kennt nur MQTT und
  `database.py`.
- **`app.py`** ist der Webserver und zugleich der Startpunkt der Anwendung: er
  liest die Datenbank über `database.py` und zeigt das Dashboard im Browser. Beim
  Start bringt er ausserdem den Sammler mit ins Spiel (dazu gleich der Thread).

Die Aufteilung ist Absicht: `database.py` weiss nichts von der Aussenwelt, der
Sammler nichts vom Web, der Webserver nichts von MQTT. Jeder Teil hat eine
Aufgabe und redet mit den anderen nur über die Datenbank, dasselbe Prinzip wie in
App 1, wo `save_kml` nichts von `build_segments` weiss. Weil die Daten dauerhaft
in `tracking.db` liegen, kann der Sammler im Hintergrund laufen, und der
Webserver kann auch vergangene Routen zeigen, wenn gerade kein Simulator fährt.

### Mehrere Dinge gleichzeitig: der Thread

Sammler und Webserver haben dasselbe Problem: beide wollen *dauerhaft* laufen.
Der MQTT-Sammler ruft `loop_forever()` auf und wartet endlos auf Nachrichten; der
Webserver ruft `app.run()` auf und wartet endlos auf Browser-Anfragen. Keiner der
beiden Aufrufe gibt von selbst je die Kontrolle zurück. Schriebe man sie
untereinander, käme die zweite Zeile nie an die Reihe, weil die erste für immer
läuft.

Ein **Thread** löst das: er ist ein zweiter Ausführungsstrang, der *neben* dem
Hauptprogramm läuft. Wir stecken den Sammler in einen Thread, sodass er endlos
horchen kann, während der Webserver im Hauptstrang ebenfalls endlos auf Anfragen
wartet. Beides läuft gleichzeitig in einem einzigen `python app.py`. Der Zusatz
`daemon=True` sorgt dafür, dass der Sammler-Thread automatisch endet, sobald das
Hauptprogramm (der Webserver) stoppt, sonst bliebe er als Geist im Hintergrund
hängen.

### Was ist eine Datenbank, und warum nicht einfach CSV?

In App 3 sind die Daten verschwunden, sobald sie durchs Terminal gescrollt sind.
Nichts wurde behalten. Für ein Dashboard, das rückblickend zeigen soll welche
Routen gefahren sind, brauchen wir aber Daten die bleiben.

Eine **Datenbank** ist im Prinzip eine schlauere CSV-Datei. **SQLite** ist eine
einzige Datei auf der Festplatte (`tracking.db`), kein Server, keine
Installation, in Python eingebaut. Der Unterschied zu CSV: man kann die Datei
nicht nur komplett lesen, sondern gezielt **befragen**: "gib mir nur die Punkte
von Container frodo" oder "wo war die Temperatur zu hoch?".

Stell dir eine Excel-Tabelle vor: Spalten (Zeitstempel, Lat, Lon, Temp, Hum,
Container, Route) und eine Zeile pro GPS-Punkt. Die Sprache zum Befragen heisst
**SQL**.

### SQL in vier Sätzen

Mehr SQL als das siehst du in der ganzen App nicht. Es liest sich fast wie
Englisch:

```sql
CREATE TABLE messages (...)              -- lege eine Tabelle mit Spalten an
INSERT INTO messages VALUES (...)        -- speichere eine Zeile
SELECT * FROM messages                   -- gib mir alle Zeilen
SELECT DISTINCT container FROM messages  -- gib mir die Container, jeden nur einmal
SELECT * FROM messages WHERE temp >= 25  -- gib mir nur die zu warmen Zeilen
```

`DISTINCT` filtert Duplikate, `WHERE` filtert nach einer Bedingung, genau das
brauchen wir fürs Dashboard.

### Was ist Flask?

In App 2 haben wir mit `requests.get(...)` einen Server **gefragt**. Flask baut
die andere Seite: einen Server, der auf Anfragen des Browsers wartet und HTML
zurückschickt.

Tippst du `http://localhost:5000` in den Browser, fragt er deinen Flask-Server:
"gib mir die Startseite". Flask schaut, welche Funktion für die Adresse `/`
zuständig ist, und schickt zurück, was diese Funktion liefert.

### Warum HTML?

Ein Browser kann nur HTML anzeigen. Genau wie ein KML-Viewer in App 1 nur KML
versteht und Folium in App 2 eine HTML-Datei erzeugt hat, muss unser Server dem
Browser HTML schicken.

HTML besteht aus **Tags** in spitzen Klammern. Fast jeder Tag kommt als Paar:
ein öffnender Tag und ein schliessender, dazwischen steht der Inhalt. Der
schliessende Tag trägt einen Schrägstrich:

```html
<tag>Inhalt</tag>
```

Den Tag selbst zeigt der Browser nie an, nur seine Wirkung auf den Text
dazwischen. Wir brauchen genau fünf:

```html
<h1>Überschrift</h1>                  <!-- grosse Überschrift -->
<ul> ... </ul>                        <!-- unsortierte Liste, umschliesst alle Einträge -->
<li>ein Eintrag</li>                  <!-- ein einzelner Listenpunkt -->
<a href="/ziel">Text</a>              <!-- anklickbarer Link -->
<span style="color:red">Text</span>   <!-- Text einfärben -->
```

Zwei dieser Tags tragen ein **Attribut**, also eine Zusatzangabe im öffnenden
Tag. Bei `<a href="/ziel">` ist `href` das Sprungziel des Links; der Text
zwischen `<a>` und `</a>` ist das, was klickbar erscheint. Bei
`<span style="color:red">` legt `style="color:red"` fest, dass der Text dazwischen
rot dargestellt wird, ohne sonst etwas zu verändern.

Wir bauen das HTML als String direkt im Python-Code zusammen, dasselbe Muster
wie in App 1, wo wir Segmente Stück für Stück gesammelt haben. Für eine einzelne
Route entsteht am Ende etwa dieser Text, den der Browser dann darstellt:

```html
<h1>Container Dashboard</h1>
<ul>
  <li><a href="/route/grp4/olten-brugg">grp4 olten-brugg</a> | 16:00 bis 16:45 | <span style="color:red">Temperaturproblem</span></li>
</ul>
```

Wichtig zu verstehen: Python kennt keine Überschriften oder Links, es klebt nur
Zeichen aneinander. Erst der Browser liest diesen Text, erkennt die Tags und
macht daraus die sichtbare Seite. So bleibt alles in einer einzigen Python-Datei
und jede Zeile ist erklärbar.

---

## Schritt 1: CSV-Struktur, was speichern wir?

Der Simulator schickt für jeden Punkt eine JSON-Nachricht (wie in App 3):

```json
{
    "timestamp": "2026-06-09 16:57:52",
    "lat": 47.3529356,
    "lon": 7.90754156,
    "temp": "24",
    "hum": "72"
}
```

Zusätzlich kommt auf dem State-Topic eine START- und eine STOP-Meldung mit dem
Routennamen:

```json
{"timestamp": "...", "action": "START", "name": "olten-brugg"}
```

Daraus ergeben sich die Spalten unserer Tabelle: `company`, `container`,
`route`, `timestamp`, `lat`, `lon`, `temp`, `hum`. Company, Container und Route
stehen nicht in der Nachricht selbst, sie kommen aus dem Topic
(`migros/grp4/...`) und aus der START-Meldung.

---

## Schritt 2: Die Datenbank (database.py)

Diese Datei hat eine Aufgabe: die Datenbank anlegen und Funktionen zum
Speichern und Lesen bereitstellen. Sie kennt weder MQTT noch Flask.

```python
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tracking.db"
```

`sqlite3` ist eingebaut, wie `csv`. `DB_PATH` zeigt auf die Datenbank-Datei im
selben Ordner, dasselbe `Path`-Muster wie in allen Apps.

### Tabelle anlegen

```python
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            company   TEXT,
            container TEXT,
            route     TEXT,
            timestamp TEXT,
            lat       REAL,
            lon       REAL,
            temp      REAL,
            hum       REAL
        )
    """)
    conn.commit()
    conn.close()
```

`sqlite3.connect()` öffnet die Datei, existiert sie noch nicht, wird sie
erstellt. Der `cursor` führt SQL-Befehle aus. `CREATE TABLE IF NOT EXISTS` legt
die Tabelle nur an, falls sie noch fehlt; beim zweiten Start passiert nichts.
Die Spalten sind wie Excel-Überschriften: `TEXT` für Wörter, `REAL` für
Dezimalzahlen. `conn.commit()` speichert wirklich, `conn.close()` macht die
Datei zu.

### Einen Punkt speichern

```python
def save_message(company, container, route, timestamp, lat, lon, temp, hum):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (company, container, route, timestamp, lat, lon, temp, hum)
    )
    conn.commit()
    conn.close()
```

`INSERT INTO messages VALUES (...)` fügt eine Zeile ein. Die `?` sind
Platzhalter, Python setzt die echten Werte sicher ein, ähnlich wie ein
f-String, nur für SQL. Wichtig: Die acht Werte stehen in derselben Reihenfolge
wie die acht Spalten oben.

### Routenübersicht lesen

```python
def get_routes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT company, container, route,
               MIN(timestamp) AS start,
               MAX(timestamp) AS end,
               MAX(CASE WHEN temp >= 25 OR hum >= 80 THEN 1 ELSE 0 END) AS has_problem
        FROM messages
        GROUP BY company, container, route
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows
```

Das ist die wichtigste Frage fürs Dashboard, übersetzt: "Gib mir jede einzigartige
Kombination von Company/Container/Route, dazu Start- und Endzeit, und ob
irgendwo die Temperatur oder Feuchtigkeit zu hoch war." `GROUP BY` fasst alle
Punkte einer Route zu einer Zeile zusammen. `has_problem` ist 1 wenn mindestens
ein Punkt den Grenzwert überschritt, sonst 0, dieselben Grenzwerte wie in der
`get_color`-Logik aus App 1.

### Punkte einer einzelnen Route lesen

```python
def get_route_points(container, route):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, lat, lon, temp, hum FROM messages WHERE container = ? AND route = ?",
        (container, route)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
```

`WHERE container = ? AND route = ?` filtert auf genau eine Route. Die `?`
funktionieren wie bei `save_message`. Die Spaltenreihenfolge ist hier wichtig:
`timestamp, lat, lon, temp, hum` ergibt `row[1]`=lat, `row[2]`=lon,
`row[3]`=temp, `row[4]`=hum, genau das, was `build_segments` aus `utils.py`
erwartet. So passt die Funktion ohne Änderung.

### Test

```bash
python -c "from database import init_db, save_message; init_db(); save_message('migros','grp4','test','2026-06-09 08:00:00',47.35,7.90,24.0,72.0); print('Gespeichert!')"
python -c "import sqlite3; c=sqlite3.connect('tracking.db'); print(c.execute('SELECT * FROM messages').fetchall())"
```

---

## Schritt 3: Daten empfangen und speichern (ingest.py)

`ingest.py` ist der Sammler aus dem Architektur-Bild: er hört dem MQTT-Broker zu
und schreibt jeden empfangenen Punkt über `save_message` in die Datenbank. Die
MQTT-Mechanik (Verbindung, Callbacks, Topics) ist dieselbe wie in App 3, sie
mündet hier nur in einen Datenbank-Eintrag statt in eine `print`-Ausgabe.

```python
import json
import paho.mqtt.client as mqtt
from database import init_db, save_message

BROKER    = "fl-17-240.zhdk.cloud.switch.ch"
PORT      = 9001
COMPANY   = "migros"
CONTAINER = "grp4"
TOPIC_MSG   = f"{COMPANY}/{CONTAINER}/message"
TOPIC_STATE = f"{COMPANY}/{CONTAINER}/state"

current_route = None
```

Oben importiert `ingest.py` die eigenen Datenbank-Funktionen (genauso, wie
`build_segments` aus `utils.py` geholt wird) und legt die Variable
`current_route` an. Sie merkt sich, welche Route gerade läuft, denn das Dashboard
soll später zeigen *welche* Route gefahren wurde, und der Routenname steht nur in
der START-Meldung, nicht in jedem GPS-Punkt. Anfangswert `None` heisst: noch
keine Route gestartet.

```python
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Verbunden mit {BROKER}")
        client.subscribe(TOPIC_MSG)
        client.subscribe(TOPIC_STATE)
    else:
        print(f"Verbindung fehlgeschlagen, Code: {rc}")
```

Sobald die Verbindung steht (`rc == 0`), abonnieren wir die zwei Topics. Erst ab
dann schickt der Broker überhaupt Nachrichten.

```python
def on_message(client, userdata, message):
    global current_route
    raw = message.payload.decode()

    if message.topic == TOPIC_STATE:
        info = json.loads(raw)
        if info.get("action") == "START":
            current_route = info.get("name")
            print(f"Route gestartet: {current_route}")
        elif info.get("action") == "STOP":
            print(f"Route beendet: {current_route}")
            current_route = None
        return

    if current_route is None:
        return

    daten = json.loads(raw)
    save_message(
        COMPANY, CONTAINER, current_route,
        daten["timestamp"],
        float(daten["lat"]), float(daten["lon"]),
        float(daten["temp"]), float(daten["hum"])
    )
    print(f"Gespeichert: {daten['timestamp']} | {daten['temp']}°C")
```

Vier Stellen lohnen den Blick:

**`global current_route`**: diese Funktion wird von paho-mqtt aufgerufen, nicht
von uns. Damit sie die äussere Variable verändern kann, muss `global` dastehen.
Ohne das würde Python eine neue, lokale Variable anlegen und die äussere bliebe
leer.

**State-Block**: kommt eine Nachricht auf dem State-Topic, merken wir uns bei
START den Routennamen in `current_route`. Bei STOP setzen wir `current_route`
wieder auf `None`. Damit gehört nach dem Ende einer Route kein Punkt mehr zu ihr:
trudelt nach dem STOP noch ein verspäteter Punkt ein, fällt er durch das
Sicherheitsnetz weiter unten und wird verworfen, statt der beendeten Route
zugeschlagen zu werden. `return` beendet die Funktion sofort, denn eine
State-Meldung ist kein GPS-Punkt.

**`if current_route is None: return`**: Sicherheitsnetz: kommen Punkte bevor
ein START kam, wissen wir nicht zu welcher Route sie gehören. Lieber wegwerfen
als falsch speichern.

**`save_message(...)`**: erreicht die Funktion diese Zeile, ist es ein echter
GPS-Punkt einer laufenden Route, und er wird gespeichert. Die acht Werte passen
zu den acht Spalten. `float()` ist Pflicht, weil Temperatur und Feuchtigkeit als
Strings ankommen, genau wie in App 1 bis 3.

```python
def start_mqtt():
    init_db()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        protocol=mqtt.MQTTv5,
        transport="websockets"
    )
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print("Verbinde...")
        client.connect(BROKER, PORT)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
        client.disconnect()
    except Exception as e:
        print(f"MQTT-Verbindung fehlgeschlagen: {e}")


if __name__ == "__main__":
    init_db()
    start_mqtt()
```

Der ganze Verbindungsaufbau steckt in einer Funktion `start_mqtt()`. Das ist der
entscheidende Punkt fürs Zusammenspiel: weil es eine Funktion ist, kann `app.py`
sie aufrufen und den Sammler mitstarten, statt `ingest.py` in einem eigenen
Terminal laufen zu lassen. `init_db()` ganz am Anfang stellt sicher, dass die
Tabelle existiert, bevor der erste Punkt kommt. `client.loop_forever()` ist die
Endlosschleife, die auf Nachrichten wartet; das `try/except` fängt Strg+C sauber
ab und gibt sonstige Verbindungsfehler als Meldung aus, statt abzustürzen.
`transport="websockets"` ist wieder entscheidend, weil der Broker nur über Port
9001 per WebSocket erreichbar ist.

Der `if __name__ == "__main__"`-Block erlaubt weiterhin, `ingest.py` allein zu
starten (`python ingest.py`), etwa zum Testen. Wird die Datei dagegen von
`app.py` importiert, läuft dieser Block nicht; dann entscheidet `app.py`, wann
`start_mqtt()` losgeht.

### Test

`ingest.py` lauscht nur, es braucht also etwas, das sendet. Das ist der Simulator
aus App 3: `--config config-switch-grp4.ini` wählt Broker und Gruppe (grp4), die
geojson-Datei ist die abzufahrende Route. Läuft kein Simulator, bleibt Terminal 2
einfach still, das ist kein Fehler, sondern fehlender Nachschub.

Zwei Terminals, beide mit aktiver venv:

```bash
# Terminal 1: der fertige Simulator aus App 3
python simulator.py --config config-switch-grp4.ini data/olten-brugg.geojson

# Terminal 2: unser neues Programm
python ingest.py
```

Im zweiten Terminal scrollen die gespeicherten Punkte durch. Danach prüfen wie
viele gelandet sind:

```bash
python -c "import sqlite3; c=sqlite3.connect('tracking.db'); r=c.execute('SELECT * FROM messages').fetchall(); print(f'{len(r)} Punkte')"
```

---

## Schritt 4: Der Webserver (app.py)

Jetzt bauen wir den Server. Wir entwickeln in zwei Etappen: erst eine nackte
Seite ("läuft Flask?"), dann die echte Funktion.

### Etappe 1: Läuft Flask überhaupt?

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hallo! Dein Server läuft."

if __name__ == "__main__":
    app.run(debug=True)
```

`Flask(__name__)` erstellt den Server. `@app.route("/")` ist ein Decorator: er
sagt Flask "wenn jemand `/` aufruft, nimm die Funktion direkt darunter". Was die
Funktion zurückgibt, sieht der Browser. `debug=True` startet den Server bei jeder
Code-Änderung automatisch neu.

```bash
python app.py
```

Im Browser `http://localhost:5000` öffnen, steht da der Text, funktioniert
Flask.

### Etappe 2: Dashboard und Karte

```python
from datetime import datetime
from flask import Flask
import threading
from database import get_routes, get_route_points, init_db
from ingest import start_mqtt
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import build_segments, get_color
import folium

app = Flask(__name__)


@app.route("/")
def index():
    routes = get_routes()
    html = "<h1>Container Dashboard</h1><ul>"
    for row in routes:
        container = row[1]
        route     = row[2]
        start     = datetime.fromisoformat(str(row[3])).strftime("%d.%m.%Y %H:%M") if row[3] else ""
        end       = datetime.fromisoformat(str(row[4])).strftime("%d.%m.%Y %H:%M") if row[4] else ""
        problem   = row[5]
        status = '<span style="color:red">Temperaturproblem</span>' if problem else '<span style="color:green">OK</span>'
        html += f'<li><a href="/route/{container}/{route}">{container} - {route}</a> | {start} bis {end} | {status}</li>'
    html += "</ul>"
    return html


@app.route("/route/<container>/<route>")
def show_route(container, route):
    rows = get_route_points(container, route)
    if not rows:
        return "<h1>Keine Daten gefunden</h1>"

    segments = build_segments(rows, get_color)
    start = segments[0][1][0]
    karte = folium.Map(location=start, zoom_start=12)
    for color, coords in segments:
        folium.PolyLine(locations=coords, color=color, weight=3).add_to(karte)

    return karte._repr_html_()


if __name__ == "__main__":
    init_db()
    threading.Thread(target=start_mqtt, daemon=True).start()
    app.run(debug=True, use_reloader=False)
```

**`get_color`** wird nicht mehr hier definiert, sondern liegt zusammen mit
`build_segments` in `utils.py` und wird oben einfach mitimportiert
(`from utils import build_segments, get_color`). So teilen sich App 2 und App 4
dieselbe Funktion, statt sie zweimal zu pflegen (siehe App 2 für die Details).
Inhaltlich ist sie identisch: Farb-Strings für Folium, dieselben Grenzwerte.

**`index()`** ruft `get_routes()` auf und baut den HTML-String Stück für Stück
zusammen: Überschrift, Liste auf, ein `<li>` pro Route, Liste zu. Der `<a>`-Link
macht jede Route anklickbar und zeigt auf `/route/grp4/olten-brugg`. Start- und
Endzeit kommen als ISO-Text aus der Datenbank;
`datetime.fromisoformat(...).strftime("%d.%m.%Y %H:%M")` macht daraus ein
lesbares Datum, und das `if row[3] else ""` fängt fehlende Werte ab.

**`show_route(container, route)`** ist der spannende Teil. Die Adresse enthält
Platzhalter `<container>` und `<route>`, Flask nimmt die Werte direkt aus der
URL und gibt sie der Funktion. Das ist genau das, was der Server in App 2 mit
seinen Endpunkten gemacht hat, nur sind wir jetzt der Server. Danach: Punkte aus
der DB holen, `build_segments(rows, get_color)` wie in App 2, Folium-Karte
bauen.

**`karte._repr_html_()`** ist der Trick, der alles einfach macht: statt die
Karte als Datei zu speichern und neu zu laden (wie in App 2), gibt Folium den
HTML-String direkt zurück. Flask schickt ihn an den Browser. Keine Datei, kein
Template-Ordner.

**`segments[0][1][0]`** ist der Startpunkt der Karte, die allererste
Koordinate, genau wie in App 2:

```python
segments[0]       # erstes Segment -> ("blue", [(lat1,lon1), ...])
segments[0][1]    # Koordinatenliste -> [(lat1,lon1), ...]
segments[0][1][0] # erste Koordinate -> (lat1, lon1)
```

**Der Start unten** bringt alles zusammen: `init_db()` legt die Tabelle an,
`threading.Thread(target=start_mqtt, daemon=True).start()` startet den Sammler im
Hintergrund (der Thread aus den Konzepten), und `app.run(...)` startet den
Webserver im Vordergrund. Ein einziger `python app.py` empfängt also Daten *und*
zeigt sie an. `use_reloader=False` ist hier wichtig: der Auto-Neustart von
`debug=True` würde den `__main__`-Block ein zweites Mal ausführen und damit einen
zweiten MQTT-Thread öffnen; das schalten wir ab.

### Test

`python app.py` starten und `http://localhost:5000` öffnen: eine Liste mit der
Route, Status und einem Link. Klick auf den Link, dann erscheint die farbige
Karte, genau wie in App 2. Weil der Reloader aus ist, nach Code-Änderungen den
Server kurz stoppen (Strg+C) und neu starten.

---

## Schritt 5: Alles zusammen betreiben

`app.py` startet den Sammler-Thread und den Webserver in einem Rutsch. Im
Live-Betrieb braucht es darum neben dem Browser nur noch den Simulator:

```
Terminal 1:  python simulator.py --config config-switch-grp4.ini data/olten-brugg.geojson
Terminal 2:  python app.py   (Sammler im Hintergrund + Webserver)
Browser:     http://localhost:5000   (zeigt das Dashboard)
```

Der Simulator sendet die Punkte, der Sammler-Thread in `app.py` schreibt sie in
die Datenbank, und derselbe `app.py`-Prozess zeigt sie im Browser. Zum reinen
Anschauen vergangener Routen reicht `app.py` ohne Simulator, die Daten liegen ja
in der Datenbank. Das ist genau die Retrospektive aus dem Challenge-Auftrag:
App 3 war der Live-Stream, der nichts behält; App 4 ist das Archiv, das alles
behält und auf Nachfrage rauskramt.

---

## Klassische Fehler

**`global` vergessen:** Ohne `global current_route` in `on_message` legt Python
eine lokale Variable an, der Routenname kommt nie nach draussen, und alle Punkte
werden mit `None` als Route gespeichert, ohne Fehlermeldung.

**`init_db()` zu spät oder gar nicht:** Wird der erste Punkt gespeichert bevor
die Tabelle existiert, gibt es einen `OperationalError: no such table`. Deshalb
ruft `start_mqtt()` `init_db()` ganz am Anfang auf.

**`commit()` vergessen:** Ohne `conn.commit()` nach `INSERT` wird nichts wirklich
gespeichert. Das Programm läuft fehlerfrei, aber die Datenbank bleibt leer, ein
besonders fieser Fehler, weil nichts abstürzt.

**Koordinatenreihenfolge:** `get_route_points` muss `lat, lon` in genau dieser
Reihenfolge liefern, damit `build_segments` und danach Folium stimmen. Stimmt die
Spaltenreihenfolge im `SELECT` nicht, landet die Route im Atlantik, derselbe
Fehler wie in App 1.

**`float()` vergessen:** Der Simulator schickt Temperatur und Feuchtigkeit als
Strings. `"24" >= 25` ergibt einen `TypeError`. Immer `float()` verwenden bevor
gerechnet oder verglichen wird.

**`transport="websockets"` vergessen:** Wie in App 3, ohne diesen Parameter
versucht paho-mqtt eine direkte TCP-Verbindung auf Port 1883, und die Verbindung
zum Broker auf Port 9001 schlägt fehl.

**Reloader öffnet den Sammler doppelt:** Liefe `app.run(debug=True)` mit
eingeschaltetem Reloader, würde der `__main__`-Block bei jeder Code-Änderung ein
zweites Mal laufen und ein zweiter MQTT-Thread entstehen. Darum
`use_reloader=False`.
