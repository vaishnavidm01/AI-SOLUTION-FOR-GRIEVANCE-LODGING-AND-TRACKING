
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

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# =========================
# INITIALIZE DATABASE
# =========================

def init_db():

    conn = get_connection()

    try:

        # Create users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                full_name TEXT NOT NULL,

                email TEXT UNIQUE NOT NULL,

                password_hash TEXT NOT NULL,

                role TEXT NOT NULL DEFAULT 'citizen'
                    CHECK(role IN ('citizen', 'admin')),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            )
        """)

        # Create grievances table
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

        # Check existing grievance columns
        columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(grievances)"
            ).fetchall()
        }

        # Add missing columns safely
        migrations = {
            "department": "TEXT DEFAULT 'Unassigned'",
            "potholes_detected": "INTEGER DEFAULT 0",
            "detection_confidence": "REAL DEFAULT 0",
            "latitude": "REAL",
            "longitude": "REAL",
            "user_id": "INTEGER REFERENCES users(id)"
        }

        for column, definition in migrations.items():

            if column not in columns:

                conn.execute(
                    f"ALTER TABLE grievances ADD COLUMN {column} {definition}"
                )

        # Index for faster citizen grievance lookup
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_grievances_user_id
            ON grievances(user_id)
        """)

        conn.commit()

    finally:
        conn.close()


# =========================
# USER MANAGEMENT
# =========================

def create_user(full_name, email, password_hash, role="citizen"):

    conn = get_connection()

    try:

        cursor = conn.execute("""
            INSERT INTO users
            (full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (
            full_name,
            email.strip().lower(),
            password_hash,
            role
        ))

        conn.commit()

        return cursor.lastrowid

    finally:
        conn.close()


def get_user_by_email(email):

    conn = get_connection()

    try:

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email.strip().lower(),)).fetchone()

        return dict(user) if user else None

    finally:
        conn.close()


def get_user_by_id(user_id):

    conn = get_connection()

    try:

        user = conn.execute("""
            SELECT id, full_name, email, role, created_at
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        return dict(user) if user else None

    finally:
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
    latitude=None,
    longitude=None,
    user_id=None
):

    conn = get_connection()

    try:

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
                longitude,
                user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            longitude,
            user_id
        ))

        conn.commit()

    finally:
        conn.close()


# =========================
# CITIZEN GRIEVANCES
# =========================

def get_user_grievances(user_id):

    conn = get_connection()

    try:

        rows = conn.execute("""
            SELECT *
            FROM grievances
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# =========================
# GET ALL GRIEVANCES - ADMIN
# =========================

def get_all_grievances():

    conn = get_connection()

    try:

        rows = conn.execute("""
            SELECT *
            FROM grievances
            ORDER BY created_at DESC
        """).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# =========================
# GPS GRIEVANCES
# =========================

def get_grievances_with_gps():

    conn = get_connection()

    try:

        rows = conn.execute("""
            SELECT grievance_id, category, latitude, longitude
            FROM grievances
            WHERE latitude IS NOT NULL
              AND longitude IS NOT NULL
        """).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()
