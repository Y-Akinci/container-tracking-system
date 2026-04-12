import paho.mqtt.client as mqtt

BROKER = "fl-17-240.zhdk.cloud.switch.ch"
PORT   = 9001
TOPIC  = "migros/grp4/olten-brugg"

TEMP_GRENZWERT     = 25
HUMIDITY_GRENZWERT = 80


def parse_message(raw):
    teile = raw.split(",")
    return {
        "timestamp": teile[0],
        "lat":       float(teile[1]),
        "lon":       float(teile[2]),
        "temp":      float(teile[3]),
        "humidity":  float(teile[4]),
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
    daten = parse_message(raw)
    print_update(daten)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Verbunden mit {BROKER}")
        print(f"Höre auf Topic: {TOPIC}")
        print("-" * 60)
        client.subscribe(TOPIC)
    else:
        print(f"Verbindung fehlgeschlagen, Code: {rc}")


client = mqtt.Client(transport="websockets")
client.on_connect = on_connect
client.on_message = on_message

print("Verbinde...")
client.connect(BROKER, PORT)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nProgramm beendet.")
    client.disconnect()