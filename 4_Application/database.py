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

def get_routes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT company, container, route,
               MIN(timestamp) AS start,
               MAX(timestamp) AS end,
               MAX(CASE WHEN temp >= 25 OR hum >= 80 THEN 1 ELSE 0 END) AS has_problem
        FROM messages
        GROUP BY company, container, route
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

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