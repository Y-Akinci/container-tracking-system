import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tracking.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            company      TEXT,
            container    TEXT,
            route        TEXT,
            timestamp    TEXT,
            lat          REAL,
            lon          REAL,
            temp         REAL,
            hum          REAL
        )
    """)
    conn.commit()
    conn.close()

def save_message(company, container, route, timestamp, lat, lon, temp, hum):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor = cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (company, container, route, timestamp, lat, lon, temp, hum)
    )
    conn.commit()
    conn.close()

    def on_message(client, userdata, message):
    raw = message.payload.decode()

    if message.topic == TOPIC_STATE:
        info = json.loads(raw)
        print(f"\n*** Transport {info.get('action')}: {info.get('name')} ***\n")
        return

    daten = json.loads(raw)
    route = message.topic.split("/")[-1] if "/" in message.topic else "unknown"

    save_message(
        COMPANY,
        CONTAINER,
        daten.get("route", "unknown"),
        daten["timestamp"],
        float(daten["lat"]),
        float(daten["lon"]),
        float(daten["temp"]),
        float(daten["hum"])
    )

    print(f"[{daten['timestamp']}] Temp: {daten['temp']}°C  Hum: {daten['hum']}% -> gespeichert")