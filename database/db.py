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

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

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
    image_filename
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO grievances
        (
            grievance_id,
            category,
            description,
            location,
            image_filename
        )

        VALUES (?, ?, ?, ?, ?)
    """, (
        grievance_id,
        category,
        description,
        location,
        image_filename
    ))

    conn.commit()

    conn.close()