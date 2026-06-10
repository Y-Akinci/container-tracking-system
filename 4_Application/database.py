import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tracking.db"

# Datenbank anlegen / Spalten erstellen
def init_db():
    conn = sqlite3.connect(DB_PATH) # öffnet Datei, falls nicht existent
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

# empfangene MQTT-Nachricht mit Route und Sensordaten in SQLite-DB speichern
def save_message(company, container, route, timestamp, lat, lon, temp, hum):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Neue Nachricht mit allen Messwerten in die Tabelle messages einfügen
    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (company, container, route, timestamp, lat, lon, temp, hum)
    )
    conn.commit()
    conn.close()

# Zusammngefasste Zeile pro Route
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

# Alle Messpunkte einer bestimmten Route holen
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