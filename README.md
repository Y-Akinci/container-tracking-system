# Container Tracking System

Python-basiertes System zur Überwachung von Transportrouten und Umgebungsbedingungen (Temperatur, Luftfeuchtigkeit). GPS-Daten werden ausgelesen, bewertet und auf interaktiven Karten visualisiert.

## Projektübersicht

Das System besteht aus vier Applikationen, die aufeinander aufbauen:

| App | Beschreibung | Datenquelle | Ausgabe |
|-----|-------------|-------------|---------|
| App 1 | GPS-Route aus CSV visualisieren | Lokale CSV-Datei | KML-Datei |
| App 2 | GPS-Route interaktiv visualisieren | REST-API (HTTP) | HTML-Karte |
| App 3 | Live GPS-Daten empfangen und anzeigen | MQTT-Broker | Terminal-Ausgabe |
| App 4 | Live GPS-Daten empfangen und speichern | MQTT-Broker | SQLite-Datenbank + Flask-API |

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
git clone <repository-url>
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
├── utils.py                    # Gemeinsame Hilfsfunktionen (build_segments)
│
├── 1_Application/              # App 1: CSV zu KML
│   ├── csv_to_kml.py
│   ├── olten-brugg (2).csv
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
│       └── requirements.txt
│
└── 4_Application/              # App 4: MQTT-Ingest + Flask-API
    ├── app.py
    ├── ingest.py
    ├── database.py
    └── requirements.txt        # noch ausstehend
```
## Applikationen

### App 1 — GPS-Route aus CSV visualisieren (KML)

Liest eine lokale CSV-Datei mit GPS-Koordinaten, Temperatur und Luftfeuchtigkeit, bewertet jeden Punkt und erzeugt eine farbige KML-Datei.

**Installation:**

```bash
cd 1_Application
pip install -r requirements.txt
```

Abhängigkeiten (`requirements.txt`):

```
simplekml==1.3.6
```

**Ausführen:**

```bash
python csv_to_kml.py
```

Die KML-Datei `olten-brugg.kml` wird im selben Ordner gespeichert. Der Browser öffnet sich automatisch auf kmlviewer.nsspot.net, dort die Datei hochladen.

### App 2 — GPS-Route interaktiv visualisieren (Folium)

Ruft GPS-Daten von einem REST-Server ab. Der Benutzer wählt im Terminal Container und Route aus. Die Route wird als interaktive HTML-Karte im Browser geöffnet.

**Installation:**

```bash
cd 2_Application
pip install -r requirements.txt
```

Abhängigkeiten (`requirements.txt`):

```
requests==2.32.5
folium==0.20.0
```

**Ausführen:**

```bash
python route_visualization_html.py
```

Der Server läuft unter `https://fl-17-240.zhdk.cloud.switch.ch`. Eine aktive Internetverbindung ist erforderlich.

### App 3 — Live GPS-Daten empfangen (MQTT-Monitor)

Empfängt GPS-Daten in Echtzeit über MQTT und zeigt Warnungen im Terminal an, wenn Temperatur- oder Feuchtigkeitsgrenzwerte überschritten werden.

**Installation (Monitor):**

```bash
cd 3_Application
pip install -r requirements.txt
```

Abhängigkeiten (`requirements.txt`):

```
paho-mqtt==2.0.0
```

**Monitor starten:**

```bash
python mqtt_monitor.py
```

**Simulator starten** (separates Terminal):

```bash
cd "3_Application/Simulator_für 3_Application"
pip install -r requirements.txt
python simulator.py --config config-switch-grp4.ini data/olten-brugg.geojson
```

Abhängigkeiten Simulator (`requirements.txt`):

```
paho-mqtt==2.0.0
requests==2.31.0
```

Der MQTT-Broker läuft unter `fl-17-240.zhdk.cloud.switch.ch` auf Port 9001 über WebSocket. Eine aktive Internetverbindung ist erforderlich.

### App 4 — MQTT-Ingest und Flask-API (in Entwicklung)

Empfängt Live-Daten über MQTT, speichert sie in einer SQLite-Datenbank und stellt sie über eine Flask-API zur Verfügung.

**Installation:**

```bash
cd 4_Application
pip install -r requirements.txt
```

**Datenbank-Ingest starten:**

```bash
python ingest.py
```

**Flask-Server starten** (separates Terminal):

```bash
python app.py
```

Die API ist erreichbar unter `http://localhost:5000`.
