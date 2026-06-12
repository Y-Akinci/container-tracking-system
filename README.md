# Container Tracking System

Python-basiertes System zur Überwachung von Transportrouten und Umgebungsbedingungen (Temperatur, Luftfeuchtigkeit). GPS-Daten werden ausgelesen, bewertet und auf interaktiven Karten visualisiert.

## Projektübersicht

Das System besteht aus vier Applikationen, die aufeinander aufbauen:

| App | Beschreibung | Datenquelle | Ausgabe |
|-----|-------------|-------------|---------|
| App 1 | GPS-Route aus CSV visualisieren | Lokale CSV-Datei | KML-Datei |
| App 2 | GPS-Route interaktiv visualisieren | REST-API (HTTP) | HTML-Karte |
| App 3 | Live GPS-Daten empfangen und anzeigen | MQTT-Broker | Terminal-Ausgabe |
| App 4 | Live GPS-Daten empfangen, speichern und visualisieren | MQTT-Broker | SQLite-Datenbank + Flask-Dashboard |

### Farbkodierung der Route

Alle Applikationen verwenden dieselbe Bewertungslogik:

| Farbe | Bedingung |
|-------|-----------|
| Blau | Temperatur < 25 °C und Feuchtigkeit < 80 % |
| Gelb | Feuchtigkeit >= 80 % |
| Orange | Temperatur >= 25 °C |
| Rot | Temperatur >= 25 °C und Feuchtigkeit >= 80 % |

## Voraussetzungen

- Python 3.10 oder neuer
- pip
- Git

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/Y-Akinci/container-tracking-system
cd container-tracking-system
```

### 2. Virtuelle Umgebung erstellen und aktivieren

```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate

# Mac / Linux
source .venv/bin/activate
```

Du erkennst die aktive Umgebung am `(.venv)`-Präfix in der Eingabezeile.

## Projektstruktur

```
container-tracking-system/
│
├── utils.py                    # Gemeinsame Hilfsfunktionen (build_segments, get_color)
│
├── 1_Application/              # App 1: CSV zu KML
│   ├── csv_to_kml.py
│   ├── olten-brugg.csv
│   └── requirements.txt
│
├── 2_Application/              # App 2: HTTP zu Folium-Karte
│   ├── route_visualization_html.py
│   └── requirements.txt
│
├── 3_Application/              # App 3: MQTT-Monitor (Terminal)
│   ├── mqtt_monitor.py
│   ├── requirements.txt
│   └── Simulator_für 3_Application/
│       ├── simulator.py
│       ├── config-switch-grp4.ini
│       ├── data/
│       │   └── *.geojson
│       └── requirements.txt
│
└── 4_Application/              # App 4: MQTT-Ingest + Flask-Dashboard
    ├── app.py
    ├── ingest.py
    ├── database.py
    └── requirements.txt
```

## Applikationen

### App 1: GPS-Route aus CSV visualisieren (KML)

Liest eine lokale CSV-Datei mit GPS-Koordinaten, Temperatur und Luftfeuchtigkeit, bewertet jeden Punkt und erzeugt eine farbige KML-Datei.

Abhängigkeiten (`1_Application/requirements.txt`):

```
simplekml==1.3.6
```

Installation und Ausführung:

```bash
cd 1_Application
pip install -r requirements.txt
python csv_to_kml.py
```

Die KML-Datei `olten-brugg.kml` wird im Ordner `1_Application/` gespeichert. Der Browser öffnet sich automatisch auf kmlviewer.nsspot.net, dort die Datei hochladen, um die Route anzuzeigen.

### App 2: GPS-Route interaktiv visualisieren (Folium)

Ruft GPS-Daten von einem REST-Server ab. Der Benutzer wählt im Terminal Container und Route aus. Die Route wird als interaktive HTML-Karte im Browser geöffnet.

Abhängigkeiten (`2_Application/requirements.txt`):

```
requests==2.32.5
folium==0.20.0
```

Installation und Ausführung:

```bash
cd 2_Application
pip install -r requirements.txt
python route_visualization_html.py
```

Der REST-Server läuft unter `https://fl-17-240.zhdk.cloud.switch.ch`. Eine aktive Internetverbindung ist erforderlich.

### App 3: Live GPS-Daten empfangen (MQTT-Monitor)

Empfängt GPS-Daten in Echtzeit über MQTT und zeigt Warnungen im Terminal an, wenn Temperatur- oder Feuchtigkeitsgrenzwerte überschritten werden.

App 3 besteht aus zwei Teilen, die in zwei separaten Terminals gestartet werden: dem Monitor und dem Simulator.

**Monitor** (Terminal 1):

Abhängigkeiten (`3_Application/requirements.txt`):

```
paho-mqtt==2.0.0
```

```bash
cd 3_Application
pip install -r requirements.txt
python mqtt_monitor.py
```

**Simulator** (Terminal 2):

Abhängigkeiten (`3_Application/Simulator_für 3_Application/requirements.txt`):

```
paho-mqtt==2.0.0
requests==2.31.0
```

```bash
cd "3_Application/Simulator_für 3_Application"
pip install -r requirements.txt
python simulator.py --config config-switch-grp4.ini data/olten-brugg.geojson
```

Der MQTT-Broker läuft unter `fl-17-240.zhdk.cloud.switch.ch` auf Port 9001 über WebSocket. Eine aktive Internetverbindung ist erforderlich.

### App 4: MQTT-Ingest und Flask-Dashboard

Empfängt Live-Daten über MQTT, speichert sie in einer SQLite-Datenbank (`tracking.db`) und stellt sie über ein Flask-Dashboard mit interaktiver Folium-Karte zur Verfügung.

Abhängigkeiten (`4_Application/requirements.txt`):

```
paho-mqtt==2.1.0
Flask==3.1.3
folium==0.20.0
```

Installation und Ausführung:

```bash
cd 4_Application
pip install -r requirements.txt
python app.py
```

`app.py` startet gleichzeitig den MQTT-Ingest-Thread und den Flask-Webserver. Das Dashboard ist erreichbar unter `http://localhost:5000`.

| Endpunkt | Beschreibung |
|----------|-------------|
| `/` | Übersicht aller empfangenen Routen mit Status |
| `/route/<container>/<route>` | Interaktive Folium-Karte der gewählten Route |

Um *live* Routen einzuspeisen und aktiv darzustellen, kann man, wie in App 3, in einem zweiten Terminal den Simulator laufen lassen (Befehl siehe App 3)

Der Simulator sendet die GPS-Punkte über MQTT, der Ingest-Thread in app.py speichert sie, und beim Neuladen des Dashboards erscheint die neue Route. Läuft kein Simulator, bleibt der Ingest-Thread still, das Dashboard funktioniert weiterhin mit den vorhandenen Daten.

Der MQTT-Broker läuft unter `fl-17-240.zhdk.cloud.switch.ch` auf Port 9001 über WebSocket. Eine aktive Internetverbindung ist erforderlich.

## Gemeinsame Hilfsfunktionen (utils.py)

Die Datei `utils.py` im Wurzelverzeichnis enthält die Funktion `build_segments`, die von App 1, App 2 und App 4 gemeinsam genutzt wird. Sie gruppiert aufeinanderfolgende GPS-Punkte mit gleicher Farbe zu Liniensegmenten.

Damit Python diese Datei findet, fügen die jeweiligen Skripte den übergeordneten Ordner zum Suchpfad hinzu:

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import build_segments
```

## Bekannte Einschränkungen

- App 2, 3 und 4 benötigen eine aktive Verbindung zum Server `fl-17-240.zhdk.cloud.switch.ch`. Ohne Verbindung starten die Applikationen nicht.




