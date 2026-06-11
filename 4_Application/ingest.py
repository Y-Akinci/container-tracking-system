import json
import paho.mqtt.client as mqtt
from database import init_db, save_message

BROKER = "fl-17-240.zhdk.cloud.switch.ch"
PORT = 9001
COMPANY = "migros"
CONTAINER = "grp4"
TOPIC_MSG = f"{COMPANY}/{CONTAINER}/message"
TOPIC_STATE = f"{COMPANY}/{CONTAINER}/state"

# Speichert Namen der aktuelle laufenden Route
current_route = None

# Wird automatisch aufgerufen, sobald Verbindung zum MQTT-Broker hergestellt wurde
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Verbunden mit {BROKER}")
        client.subscribe(TOPIC_MSG)
        client.subscribe(TOPIC_STATE)
    else:
        print(f"Verbindung fehlgeschlagen, Code: {rc}")

# Wird automatisch aufgerufen, sobald MQTT-Nachricht empfangen wird
def on_message(client, userdata, message):

    global current_route

    # Nutzlast zu Json-String
    raw = message.payload.decode()

    if message.topic == TOPIC_STATE:

        # Json-String zu Python-Dictionary
        info = json.loads(raw)

        if info.get("action") == "START":
            current_route = info.get("name")
            print(f"Route gestartet: {current_route}")
        elif info.get("action") == "STOP":
            print(f"Route beendet: {current_route}")
            # Route zurücksetzen, damit keine verspäteten Nachrichten gespeichert werden
            current_route = None
        return

    if current_route is None:
        return

    daten = json.loads(raw)
    save_message(
        COMPANY,
        CONTAINER,
        current_route,
        daten["timestamp"],
        float(daten["lat"]),
        float(daten["lon"]),
        float(daten["temp"]),
        float(daten["hum"])
    )
    print(f"Gespeichert: {daten['timestamp']} | {daten['temp']}°C")

def start_mqtt():
    init_db() # DB / Tabelle wird erstellt

    # MQTT-Client ertsellen (Verbindungsobjekt)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5, transport="websockets")
    
    # Funktion on_connect & on_message mit MQTT-Client verknüpfen
    client.on_connect = on_connect
    client.on_message = on_message

    # Verbindet den MQTT-Client mit dem Broker und wartet dauerhaft auf neue Nachrichten.
    try:
        print("Verbinde...")
        client.connect(BROKER, PORT)
        client.loop_forever()

    except KeyboardInterrupt:
        # Wird ausgeführt, wenn das Programm mit Ctrl+C beendet wird.
        print("\nBeendet.")
        client.disconnect()

    except Exception as e:
        # Fängt andere Verbindungsfehler ab und gibt die Fehlermeldung aus.
        print(f"MQTT-Verbindung fehlgeschlagen: {e}")

# Nur ausführen, wenn ingest.py direkt gestartet wird
if __name__ == "__main__":
    init_db()
    start_mqtt()