import json
import paho.mqtt.client as mqtt

BROKER    = "fl-17-240.zhdk.cloud.switch.ch"
PORT      = 9001
TOPIC_MSG = "migros/grp4/message"
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
    print(f"[{daten['timestamp']}]  Temp: {daten['temp']}°C  Feuchtigkeit: {daten['humidity']}%  →  {status}")


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