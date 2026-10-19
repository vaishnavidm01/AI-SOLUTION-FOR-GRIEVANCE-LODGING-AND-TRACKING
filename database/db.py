import sqlite3
from pathlib import Path


# =========================
# DATABASE LOCATION
# =========================

DB_PATH = Path(__file__).resolve().parent / "grievances.db"


# =========================
# DATABASE CONNECTION
# =========================

def get_connection():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


# =========================
# CREATE DATABASE TABLE
# =========================

def init_db():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS grievances (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            grievance_id TEXT UNIQUE NOT NULL,

            category TEXT NOT NULL,

            description TEXT NOT NULL,

            location TEXT,

            image_filename TEXT,

            status TEXT DEFAULT 'Submitted',

            severity TEXT DEFAULT 'Pending',

            department TEXT DEFAULT 'Unassigned',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)
    # Add department column to existing databases if needed
    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(grievances)"
        ).fetchall()
    ]

    if "department" not in columns:
        conn.execute(
            "ALTER TABLE grievances ADD COLUMN department TEXT DEFAULT 'Unassigned'"
        )
    # Add YOLO detection columns to existing databases if needed
    if "potholes_detected" not in columns:
        conn.execute(
            "ALTER TABLE grievances ADD COLUMN potholes_detected INTEGER DEFAULT 0"
        )

    if "detection_confidence" not in columns:
        conn.execute(
            "ALTER TABLE grievances ADD COLUMN detection_confidence REAL DEFAULT 0"
        )
    # Add GPS coordinate columns to existing databases if needed
    if "latitude" not in columns:
        conn.execute(
            "ALTER TABLE grievances ADD COLUMN latitude REAL"
        )

    if "longitude" not in columns:
        conn.execute(
            "ALTER TABLE grievances ADD COLUMN longitude REAL"
        )

    conn.commit()

    conn.close()


# =========================
# INSERT GRIEVANCE
# =========================



def insert_grievance(
    grievance_id,
    category,
    description,
    location,
    image_filename,
    severity,
    department,
    potholes_detected=0,
    detection_confidence=0.0,
    latitude = None,
    longitude = None
):
    conn = get_connection()

    conn.execute("""
        INSERT INTO grievances
        (
            grievance_id,
            category,
            description,
            location,
            image_filename,
            severity,
            department,
            potholes_detected,
            detection_confidence,
            latitude,
            longitude
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        grievance_id,
        category,
        description,
        location,
        image_filename,
        severity,
        department,
        potholes_detected,
        detection_confidence,
        latitude,
        longitude
    ))

    conn.commit()
    conn.close()

def get_grievances_with_gps():
    conn = get_connection()

    rows = conn.execute("""
        SELECT grievance_id, category, latitude, longitude
        FROM grievances
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]
