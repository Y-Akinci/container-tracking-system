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
