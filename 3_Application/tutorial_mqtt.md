# Python Tutorial: Live GPS-Daten empfangen mit MQTT

Wir haben im Modul CDE1 ein Container-Tracking-System gebaut. Für App 3 mussten wir GPS-Daten nicht aus einer Datei lesen, sondern live empfangen während der Container fährt. Dafür haben wir MQTT verwendet. Dieses Tutorial erklärt was MQTT ist, warum wir es gewählt haben, und wie du den Code selbst nachbauen kannst.

## Voraussetzungen

Du solltest bereits wissen was das bedeutet:

```python
if temp >= 25:
    print("zu warm")

for row in data:
    print(row)

def meine_funktion(wert):
    return wert * 2
```

## Schritt 1: Was ist MQTT und warum haben wir es verwendet

### Das Problem mit HTTP

In App 1 haben wir eine fertige CSV-Datei gelesen. Die Daten waren schon da, wir mussten sie nur verarbeiten. Aber was wenn der Container noch fährt und wir die Daten live sehen wollen?

Mit HTTP müsste unser Programm immer wieder beim Server anfragen: "Gibt es was Neues?" Das ist ineffizient, weil meistens die Antwort "nein" ist und trotzdem jedes Mal eine Verbindung aufgebaut wird.

### Die Lösung: MQTT

MQTT ist ein Protokoll das für genau diesen Fall gebaut wurde, live Daten von Sensoren und Geräten übertragen. Es funktioniert nach dem Prinzip "publish und subscribe", also veröffentlichen und abonnieren.

Stell dir ein Radio vor. Der Sender publiziert Musik auf einer bestimmten Frequenz. Wer zuhören will, stellt sein Radio auf diese Frequenz ein und abonniert sie. Der Sender muss nicht wissen wer zuhört, und der Zuhörer muss nicht beim Sender anfragen.

Genau so funktioniert MQTT:

Der Simulator ist der Sender. Er verbindet sich mit einem Broker und publiziert Daten auf einem Topic. Unser Monitor ist der Empfänger. Er verbindet sich mit demselben Broker und abonniert dasselbe Topic. Sobald der Simulator etwas schickt, bekommt der Monitor es sofort.

### Was ist ein Broker?

Der Broker ist der Mittelsmann. Er nimmt Nachrichten von Publishern entgegen und leitet sie an alle Subscriber weiter die das Topic abonniert haben. In unserem Projekt läuft der Broker auf dem Server des Dozenten:

```
fl-17-240.zhdk.cloud.switch.ch
Port 9001 über WebSocket
```

### Was ist ein Topic?

Ein Topic ist wie eine Adresse für Nachrichten. Es ist ein Text mit Schrägstrichen als Trennzeichen, ähnlich wie ein Dateipfad. In unserem Projekt:

```
migros/grp4/message   <- hier kommen die GPS-Datenpunkte an
migros/grp4/state     <- hier kommen Start und Stop Meldungen an
```

Das Format ist `{company}/{container}/{typ}`. So können viele verschiedene Container gleichzeitig laufen ohne sich zu stören.

## Schritt 2: Das Package paho-mqtt

Wir hätten das MQTT-Protokoll von Hand implementieren können, aber das wäre sehr aufwändig. `paho-mqtt` ist das offizielle Python Package für MQTT und wird von der MQTT-Organisation selbst gepflegt.

### Installation

```bash
pip install paho-mqtt
```

### Wie man es einbindet

```python
import paho.mqtt.client as mqtt
```

Wir importieren nur den `client` Teil des Packages, weil wir nur die Client-Funktionalität brauchen und nicht den ganzen Rest.

## Schritt 3: Was der Simulator schickt

Bevor wir den Monitor schreiben, müssen wir verstehen was der Simulator überhaupt schickt. Der Simulator liest eine GeoJSON-Datei mit GPS-Punkten, fügt Temperatur und Feuchtigkeit hinzu, und schickt für jeden Punkt eine JSON-Nachricht.

### Das Nachrichtenformat

Für jeden GPS-Punkt schickt der Simulator eine Nachricht auf dem Topic `migros/grp4/message`:

```json
{
    "timestamp": "2026-03-09 14:35:56",
    "lat": 47.3529356,
    "lon": 7.90754156,
    "temp": "24",
    "hum": "72"
}
```

Zusätzlich schickt er auf dem Topic `migros/grp4/state` eine Start-Meldung wenn er beginnt und eine Stop-Meldung wenn er fertig ist:

```json
{"timestamp": "2026-03-09 14:35:56", "action": "START", "name": "olten-brugg"}
{"timestamp": "2026-03-09 16:17:41", "action": "STOP",  "name": "olten-brugg"}
```

### Was ist JSON?

JSON ist ein Textformat für strukturierte Daten. Anders als CSV wo alles durch Kommas getrennt ist, hat JSON Schlüssel und Werte wie ein Python-Dictionary. In Python liest man JSON so:

```python
import json

text = '{"temp": "24", "hum": "72"}'
daten = json.loads(text)   # Text zu Dictionary
print(daten["temp"])       # gibt "24" aus
```

`json.loads()` verwandelt einen JSON-String in ein Python-Dictionary. Das "s" in `loads` steht für "string".

## Schritt 4: Den Monitor aufbauen

### Callbacks, was sind das?

MQTT arbeitet mit sogenannten Callbacks. Das sind Funktionen die wir definieren und die automatisch aufgerufen werden wenn etwas passiert, zum Beispiel wenn eine Verbindung aufgebaut wird oder wenn eine Nachricht ankommt.

Wir schreiben die Funktion, aber wir rufen sie nicht selbst auf. Wir sagen paho-mqtt: "Wenn eine Nachricht ankommt, ruf bitte diese Funktion auf." paho-mqtt kümmert sich um den Rest.

### Verbindung aufbauen mit on_connect

```python
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Verbunden!")
        client.subscribe("migros/grp4/message")
        client.subscribe("migros/grp4/state")
    else:
        print(f"Verbindung fehlgeschlagen, Code: {rc}")
```

Diese Funktion wird aufgerufen sobald die Verbindung zum Broker steht. `rc` steht für "return code", also 0 bedeutet Erfolg. Erst wenn wir verbunden sind abonnieren wir die Topics.

Warum erst in `on_connect` und nicht vorher? Weil man Topics nur abonnieren kann wenn man bereits verbunden ist. Würde man es vorher tun, käme eine Fehlermeldung.

### Nachrichten verarbeiten mit on_message

```python
def on_message(client, userdata, message):
    raw = message.payload.decode()

    if message.topic == "migros/grp4/state":
        info = json.loads(raw)
        print(f"\n*** Transport {info.get('action')}: {info.get('name')} ***\n")
        return

    daten = parse_message(raw)
    print_update(daten)
```

`message.payload` ist die rohe Nachricht als Bytes. Mit `.decode()` wird sie zu einem String. Dann schauen wir auf welchem Topic die Nachricht kam und reagieren entsprechend.

### Nachrichten auslesen

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

Wir parsen die JSON-Nachricht und wandeln die Werte in die richtigen Typen um. Temperatur und Feuchtigkeit kommen als Strings an, deshalb `float()`.

### Warnstatus bestimmen

```python
def get_status(temp, humidity):
    if temp >= 25 and humidity >= 80:
        return "WARNUNG: Temperatur UND Feuchtigkeit zu hoch!"
    elif temp >= 25:
        return "WARNUNG: Temperatur zu hoch!"
    elif humidity >= 80:
        return "WARNUNG: Feuchtigkeit zu hoch!"
    else:
        return "OK"
```

Diese Logik kennst du schon aus App 1. Dieselben Grenzwerte, dieselbe Struktur.

### Ausgabe im Terminal

```python
def print_update(daten):
    status = get_status(daten["temp"], daten["humidity"])
    print(f"[{daten['timestamp']}]  Temp: {daten['temp']}°C  Feuchtigkeit: {daten['humidity']}%  ->  {status}")
```

## Schritt 5: Client erstellen und verbinden

```python
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    protocol=mqtt.MQTTv5,
    transport="websockets"
)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT)
```

Hier sind drei Dinge wichtig:

`CallbackAPIVersion.VERSION2` sagt paho-mqtt welche Version der Callback-Schnittstelle wir verwenden. Das muss zur Version des Packages passen.

`protocol=mqtt.MQTTv5` ist die Version des MQTT-Protokolls. Version 5 ist die aktuelle.

`transport="websockets"` ist entscheidend. Unser Broker ist über Port 9001 erreichbar, aber nur über WebSocket. Ohne diesen Parameter versucht paho-mqtt eine direkte TCP-Verbindung auf Port 1883, was nicht funktioniert.

### loop_forever

```python
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nProgramm beendet.")
    client.disconnect()
```

`loop_forever()` startet eine Endlosschleife die auf neue Nachrichten wartet. Sie läuft bis wir Ctrl+C drücken. `KeyboardInterrupt` ist die Exception die Python wirft wenn Ctrl+C gedrückt wird. Wir fangen sie ab um das Programm sauber zu beenden.

## Schritt 6: Den Simulator starten

Der Simulator liest eine GeoJSON-Datei und sendet die Punkte Schritt für Schritt an den Broker. Er braucht eine Config-Datei die sagt wohin er sich verbinden soll.

### Config-Datei erstellen

Erstelle eine Datei `config-switch-grp4.ini` im Simulator-Ordner:

```
[DEFAULT]
company = migros
container = grp4

[log]
level = debug

[mqtt]
broker = fl-17-240.zhdk.cloud.switch.ch
port = 9001
transport = websockets
token =

[simulation]
profile = 0.0,24,72;0.2,25,70;0.4,26.5,65;0.7,27,80;0.9,27.5,75
clock-rate = 0.01
```

Das `profile` beschreibt wie sich Temperatur und Feuchtigkeit über die Route verändern. Das Format ist `position,temperatur,feuchtigkeit` wobei die Position ein Wert zwischen 0.0 (Start) und 1.0 (Ende) ist. Bei 20% der Strecke wechselt es zum nächsten Profil, usw.

`clock-rate = 0.01` bedeutet dass der Simulator sehr schnell läuft. 0.01 Sekunden zwischen jedem Punkt. Für einen echten Test würde man 5 Sekunden wählen, aber für die Demo ist schnell besser.

### Simulator starten

```bash
python simulator.py --config config-switch-grp4.ini data/olten-brugg.geojson
```

### Monitor starten in einem zweiten Terminal

```bash
python mqtt_monitor.py
```

## Schritt 7: Vollständiger Monitor-Code

```python
import json
import paho.mqtt.client as mqtt

BROKER      = "fl-17-240.zhdk.cloud.switch.ch"
PORT        = 9001
TOPIC_MSG   = "migros/grp4/message"
TOPIC_STATE = "migros/grp4/state"

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

## Klassische Fehler aus unserer eigenen Erfahrung

**`transport="websockets"` vergessen:** Ohne diesen Parameter versucht paho-mqtt eine direkte TCP-Verbindung. Port 9001 ist aber nur über WebSocket erreichbar, deshalb schlägt die Verbindung einfach fehl ohne klare Fehlermeldung.

**`CallbackAPIVersion.VERSION2` fehlt:** Neuere Versionen von paho-mqtt verlangen diese Angabe. Ohne sie kommt eine Warnung oder ein Fehler wegen der falschen Callback-Signatur.

**Topic falsch:** Gross- und Kleinschreibung ist bei Topics wichtig. `migros/grp4/message` und `migros/GRP4/message` sind zwei verschiedene Topics.

**Nachrichten kommen nicht an:** Meistens liegt es daran dass der Simulator noch nicht gestartet wurde, oder dass Topic im Monitor und Topic im Simulator nicht übereinstimmen.

**`float()` vergessen:** Der Simulator schickt Temperatur und Feuchtigkeit als Strings im JSON. `"24" >= 25` ergibt in Python einen TypeError. Immer `float()` verwenden bevor du mit den Werten rechnest.
