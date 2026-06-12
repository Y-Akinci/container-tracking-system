# Python Tutorial: Live GPS-Daten empfangen mit MQTT

Für App 3 mussten wir GPS-Daten nicht aus einer Datei lesen, sondern live empfangen während der Container fährt. Dafür haben wir MQTT verwendet. Dieses Tutorial erklärt was MQTT ist, warum wir es gewählt haben, und wie du den Code selbst nachbauen kannst.

Die Live-Daten liefert dabei ein Simulator: ein bereits fertiges Programm, das uns im Repository vorliegt. Er liest eine Streckendatei und sendet ihre GPS-Punkte über MQTT, als würde ein echter Container die Route fahren. Unsere Aufgabe ist die Empfängerseite, der Monitor.

**Lerninhalt:** 
Wie empfängt man GPS-Daten live über MQTT, bewertet sie nach Kriterien (Temperatur, Luftfeuchtigkeit) und gibt den Status in Echtzeit im Terminal aus?

---

## Voraussetzungen

Du kennst bereits folgende Konzepte aus App 1 und 2:

- Funktionen (`def`, `return`)
- Listen und Dictionaries
- `for`-Schleifen und `enumerate`
- `if`, `elif`, `else`
- `float()` für Typumwandlung
- `pathlib` für Dateipfade
- Die Logik von `get_color` und `build_segments`
- HTTP-Requests mit `requests`
- JSON als Datenformat
- Interaktive Karten mit `folium`
- Fehlerbehandlung mit `try/except`
- Simulator

Neu in diesem Tutorial:

- App 3 empfängt GPS-Daten live über MQTT statt aus einer fertigen Datei.
- Der Simulator veröffentlicht JSON-Nachrichten an einen Broker, der Monitor abonniert die Topics.
- Es erklärt paho-mqtt, die Topics migros/grp4/message und migros/grp4/state, sowie JSON-Parsing und Typumwandlung.
- Wichtige Punkte sind WebSocket-Verbindung auf Port 9001 und typische Fehler wie falsches Topic oder fehlendes transport="websockets".

## Packages installieren
```
---
## 

```bash
pip install paho-mqtt
pip freeze > requirements.txt
```

`json` ist in Python eingebaut, kein `pip` nötig.

---

## Konzepte

### Was ist MQTT und warum haben wir es verwendet

#### Das Problem mit HTTP

In App 1 haben wir eine fertige CSV-Datei gelesen. Die Daten waren schon da, wir mussten sie nur verarbeiten. Aber was wenn der Container noch fährt und wir die Daten live sehen wollen?

Mit HTTP müsste unser Programm immer wieder beim Server anfragen: "Gibt es was Neues?" Das ist ineffizient, weil meistens die Antwort "nein" ist und trotzdem jedes Mal eine Verbindung aufgebaut wird.

#### Die Lösung: MQTT

MQTT ist ein Protokoll das für genau diesen Fall gebaut wurde, live Daten von Sensoren und Geräten übertragen. Es funktioniert nach dem Prinzip "publish und subscribe", also veröffentlichen und abonnieren.

Stell dir ein Radio vor. Der Sender publiziert Musik auf einer bestimmten Frequenz. Wer zuhören will, stellt sein Radio auf diese Frequenz ein und abonniert sie. Der Sender muss nicht wissen wer zuhört, und der Zuhörer muss nicht beim Sender anfragen.

Genau so funktioniert MQTT:

Der Simulator ist der Sender. Er verbindet sich mit einem Broker und publiziert Daten auf einem Topic. Unser Monitor ist der Empfänger. Er verbindet sich mit demselben Broker und abonniert dasselbe Topic. Sobald der Simulator etwas schickt, bekommt der Monitor es sofort.

#### Was ist ein Broker?

Der Broker ist der Mittelsmann. Er nimmt Nachrichten von Publishern entgegen und leitet sie an alle Subscriber weiter die das Topic abonniert haben. In unserem Projekt läuft der Broker auf dem Server des Dozenten:

```
fl-17-240.zhdk.cloud.switch.ch
Port 9001 über WebSocket
```

#### Was ist ein Topic?

Ein Topic ist wie eine Adresse für Nachrichten. Es ist ein Text mit Schrägstrichen als Trennzeichen, ähnlich wie ein Dateipfad. In unserem Projekt:

```
migros/grp4/message   <- hier kommen die GPS-Datenpunkte an
migros/grp4/state     <- hier kommen Start und Stop Meldungen an
```

Das Format ist `{company}/{container}/{typ}`. So können viele verschiedene Container gleichzeitig laufen ohne sich zu stören.

---
Wir importieren nur den `client` Teil des Packages, weil wir nur die Client-Funktionalität brauchen.

### Was der Simulator schickt

Bevor wir den Monitor schreiben, müssen wir verstehen was der Simulator sendet. Für jeden GPS-Punkt schickt er eine JSON-Nachricht auf dem Topic `migros/grp4/message`:

```json
{
    "timestamp": "2026-03-09 14:35:56",
    "lat": 47.3529356,
    "lon": 7.90754156,
    "temp": "24",
    "hum": "72"
}
```

Zusätzlich schickt er auf dem Topic `migros/grp4/state` eine Start- und eine Stop-Meldung:

```json
{"timestamp": "2026-03-09 14:35:56", "action": "START", "name": "olten-brugg"}
{"timestamp": "2026-03-09 16:17:41", "action": "STOP",  "name": "olten-brugg"}
```
---
Package installieren

bashpip install paho-mqtt
pip freeze > requirements.txt

```python
import paho.mqtt.client as mqtt
```
---
## Schritt 1: Konstanten definieren

Ganz oben im Script legen wir alle fixen Werte fest, damit wir sie nur an einem Ort ändern müssen:

```python
import json
import paho.mqtt.client as mqtt

BROKER             = "fl-17-240.zhdk.cloud.switch.ch"
PORT               = 9001
TOPIC_MSG          = "migros/grp4/message"
TOPIC_STATE        = "migros/grp4/state"
TEMP_GRENZWERT     = 25
HUMIDITY_GRENZWERT = 80
```

## Schritt 2: Nachrichten parsen

`message.payload` kommt als Bytes an. Mit `.decode()` wird es ein String, mit `json.loads()` ein Dictionary. Temperatur und Feuchtigkeit kommen als Strings an, deshalb `float()`:

```python
def parse_message(raw):
    daten = json.loads(raw)
    return {
        "timestamp": daten["timestamp"],
        "lat":       float(daten["lat"]),
        "lon":       float(daten["lon"]),
        "temp":      float(daten["temp"]),
        "humidity":  float(daten["hum"]),
    }
```

## Schritt 3: Warnstatus bestimmen

Die Logik ist dieselbe wie in App 1. Dieselben Grenzwerte, dieselbe Struktur:

```python
def get_status(temp, humidity):
    if temp >= TEMP_GRENZWERT and humidity >= HUMIDITY_GRENZWERT:
        return "WARNUNG: Temperatur UND Feuchtigkeit zu hoch!"
    elif temp >= TEMP_GRENZWERT:
        return "WARNUNG: Temperatur zu hoch!"
    elif humidity >= HUMIDITY_GRENZWERT:
        return "WARNUNG: Feuchtigkeit zu hoch!"
    else:
        return "OK"
```

## Schritt 4: Ausgabe im Terminal

```python
def print_update(daten):
    status = get_status(daten["temp"], daten["humidity"])
    print(f"[{daten['timestamp']}]  Temp: {daten['temp']}°C  Feuchtigkeit: {daten['humidity']}%  ->  {status}")
```

## Schritt 5: Callbacks definieren

MQTT arbeitet mit Callbacks. Das sind Funktionen die wir definieren, aber nicht selbst aufrufen. Wir sagen paho-mqtt: "Wenn eine Verbindung aufgebaut wird, ruf diese Funktion auf." paho-mqtt kümmert sich um den Rest.

`on_connect` wird aufgerufen sobald die Verbindung zum Broker steht. Erst dann abonnieren wir die Topics, weil man Topics nur abonnieren kann wenn man bereits verbunden ist:

```python
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Verbunden mit {BROKER}")
        print(f"Höre auf: {TOPIC_MSG}")
        print("-" * 60)
        client.subscribe(TOPIC_MSG)
        client.subscribe(TOPIC_STATE)
    else:
        print(f"Verbindung fehlgeschlagen, Code: {rc}")
```

`on_message` wird aufgerufen sobald eine Nachricht ankommt. Wir schauen zuerst auf welchem Topic sie ankam und reagieren entsprechend:

```python
def on_message(client, userdata, message):
    raw = message.payload.decode()

    if message.topic == TOPIC_STATE:
        info = json.loads(raw)
        print(f"\n*** Transport {info.get('action')}: {info.get('name')} ***\n")
        return

    daten = parse_message(raw)
    print_update(daten)
```

## Schritt 6: Client erstellen und verbinden

Hier sind drei Dinge wichtig:

`CallbackAPIVersion.VERSION2` sagt paho-mqtt welche Version der Callback-Schnittstelle wir verwenden. Das muss zur installierten Version des Packages passen.

`protocol=mqtt.MQTTv5` gibt die MQTT-Protokollversion an. Version 5 ist die aktuelle.

`transport="websockets"` ist entscheidend. Unser Broker ist über Port 9001 erreichbar, aber nur über WebSocket. Ohne diesen Parameter versucht paho-mqtt eine direkte TCP-Verbindung auf Port 1883, was nicht funktioniert.

```python
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    protocol=mqtt.MQTTv5,
    transport="websockets"
)
client.on_connect = on_connect
client.on_message = on_message

print("Verbinde...")
client.connect(BROKER, PORT)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nProgramm beendet.")
    client.disconnect()
```

`loop_forever()` startet eine Endlosschleife die auf neue Nachrichten wartet. Sie läuft bis wir Ctrl+C drücken. `KeyboardInterrupt` ist die Exception die Python wirft wenn Ctrl+C gedrückt wird. Wir fangen sie ab um das Programm sauber zu beenden.

## Schritt 7: Simulator starten

Den Simulator musst du nicht selbst schreiben. Er ist bereits fertig im Repository enthalten und wird dir zusammen mit diesem Tutorial mitgeliefert. Wie er intern funktioniert, wird weiter unten im Abschnitt "Wie der Simulator funktioniert" erklärt.

Der Simulator befindet sich unter `3_Application/Simulator_für_3_Application/`. Er liest eine GeoJSON-Datei und sendet die Punkte Schritt für Schritt über MQTT an den Broker.

Die Config-Datei `config-switch-grp4.ini` ist bereits im Ordner vorhanden. Die wichtigsten Werte darin:

```ini
[DEFAULT]
company = migros
container = grp4

[mqtt]
broker = fl-17-240.zhdk.cloud.switch.ch
port = 9001
transport = websockets

[simulation]
profile = 0.0,24,72;0.2,25,70;0.4,26.5,65;0.7,27,80;0.9,27.5,75
clock-rate = 0.01
```

`profile` beschreibt wie sich Temperatur und Feuchtigkeit über die Route verändern. Das Format ist `position,temperatur,feuchtigkeit`, wobei die Position ein Wert zwischen 0.0 (Start) und 1.0 (Ende) ist. `clock-rate = 0.01` bedeutet 0.01 Sekunden zwischen jedem Punkt, damit die Demo schnell durchläuft.

Simulator starten:

```bash
cd "3_Application/Simulator_für_3_Application"
python simulator.py --config config-switch-grp4.ini data/olten-brugg.geojson
```

Monitor in einem zweiten Terminal starten:

```bash
cd 3_Application
python mqtt_monitor.py
```

## Vollständiger Code

```python
import json
import paho.mqtt.client as mqtt

BROKER             = "fl-17-240.zhdk.cloud.switch.ch"
PORT               = 9001
TOPIC_MSG          = "migros/grp4/message"
TOPIC_STATE        = "migros/grp4/state"
TEMP_GRENZWERT     = 25
HUMIDITY_GRENZWERT = 80


def parse_message(raw):
    daten = json.loads(raw)
    return {
        "timestamp": daten["timestamp"],
        "lat":       float(daten["lat"]),
        "lon":       float(daten["lon"]),
        "temp":      float(daten["temp"]),
        "humidity":  float(daten["hum"]),
    }


def get_status(temp, humidity):
    if temp >= TEMP_GRENZWERT and humidity >= HUMIDITY_GRENZWERT:
        return "WARNUNG: Temperatur UND Feuchtigkeit zu hoch!"
    elif temp >= TEMP_GRENZWERT:
        return "WARNUNG: Temperatur zu hoch!"
    elif humidity >= HUMIDITY_GRENZWERT:
        return "WARNUNG: Feuchtigkeit zu hoch!"
    else:
        return "OK"


def print_update(daten):
    status = get_status(daten["temp"], daten["humidity"])
    print(f"[{daten['timestamp']}]  Temp: {daten['temp']}°C  Feuchtigkeit: {daten['humidity']}%  ->  {status}")


def on_message(client, userdata, message):
    raw = message.payload.decode()

    if message.topic == TOPIC_STATE:
        info = json.loads(raw)
        print(f"\n*** Transport {info.get('action')}: {info.get('name')} ***\n")
        return

    daten = parse_message(raw)
    print_update(daten)


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Verbunden mit {BROKER}")
        print(f"Höre auf: {TOPIC_MSG}")
        print("-" * 60)
        client.subscribe(TOPIC_MSG)
        client.subscribe(TOPIC_STATE)
    else:
        print(f"Verbindung fehlgeschlagen, Code: {rc}")


client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    protocol=mqtt.MQTTv5,
    transport="websockets"
)
client.on_connect = on_connect
client.on_message = on_message

print("Verbinde...")
client.connect(BROKER, PORT)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nProgramm beendet.")
    client.disconnect()
```
---

## Klassische Fehler aus unserer eigenen Erfahrung

**`transport="websockets"` vergessen:** Ohne diesen Parameter versucht paho-mqtt eine direkte TCP-Verbindung. Port 9001 ist aber nur über WebSocket erreichbar, deshalb schlägt die Verbindung einfach fehl ohne klare Fehlermeldung.

**`CallbackAPIVersion.VERSION2` fehlt:** Neuere Versionen von paho-mqtt verlangen diese Angabe. Ohne sie kommt eine Warnung oder ein Fehler wegen der falschen Callback-Signatur.

**Topic falsch:** Gross- und Kleinschreibung ist bei Topics wichtig. `migros/grp4/message` und `migros/GRP4/message` sind zwei verschiedene Topics.

**Nachrichten kommen nicht an:** Meistens liegt es daran dass der Simulator noch nicht gestartet wurde, oder dass Topic im Monitor und Topic im Simulator nicht übereinstimmen.

**`float()` vergessen:** Der Simulator schickt Temperatur und Feuchtigkeit als Strings im JSON. `"24" >= 25` ergibt in Python einen TypeError. Immer `float()` verwenden bevor du mit den Werten rechnest.
