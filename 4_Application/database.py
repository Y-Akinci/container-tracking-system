import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tracking.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
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


def save_message(company, container, route, timestamp, lat, lon, temp, hum):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (company, container, route, timestamp, lat, lon, temp, hum)
    )
    conn.commit()
    conn.close()