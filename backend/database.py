from __future__ import annotations
import sqlite3
from datetime import date
from config import SQLITE_PATH


def get_connection():
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TEXT DEFAULT (datetime('now')),
            lookup_count_today INTEGER DEFAULT 0,
            last_lookup_date TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS lookups (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            video_id TEXT,
            timestamp_seconds REAL,
            location_name TEXT,
            region TEXT,
            country TEXT,
            lat REAL,
            lon REAL,
            confidence TEXT,
            evidence_json TEXT,
            maps_url TEXT,
            status TEXT DEFAULT 'complete',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS cache (
            video_id TEXT,
            timestamp_bucket INTEGER,
            result_json TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (video_id, timestamp_bucket)
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lookup_id TEXT,
            user_id TEXT,
            vote TEXT,
            correct_location TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)


def get_or_create_user(conn: sqlite3.Connection, user_id: str):
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return dict(row)
    conn.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    return {"user_id": user_id, "lookup_count_today": 0, "last_lookup_date": ""}


def check_rate_limit(conn: sqlite3.Connection, user_id: str, limit: int) -> bool:
    user = get_or_create_user(conn, user_id)
    today = date.today().isoformat()
    if user["last_lookup_date"] != today:
        conn.execute(
            "UPDATE users SET lookup_count_today = 0, last_lookup_date = ? WHERE user_id = ?",
            (today, user_id)
        )
        conn.commit()
        return True
    return user["lookup_count_today"] < limit


def increment_lookup_count(conn: sqlite3.Connection, user_id: str):
    today = date.today().isoformat()
    conn.execute(
        "UPDATE users SET lookup_count_today = lookup_count_today + 1, last_lookup_date = ? WHERE user_id = ?",
        (today, user_id)
    )
    conn.commit()


def get_cached_result(conn: sqlite3.Connection, video_id: str, timestamp: float, tolerance: int):
    bucket = int(timestamp // tolerance) * tolerance
    row = conn.execute(
        "SELECT result_json FROM cache WHERE video_id = ? AND timestamp_bucket = ?",
        (video_id, bucket)
    ).fetchone()
    return row["result_json"] if row else None


def save_cache(conn: sqlite3.Connection, video_id: str, timestamp: float, tolerance: int, result_json: str):
    bucket = int(timestamp // tolerance) * tolerance
    conn.execute(
        "INSERT OR REPLACE INTO cache (video_id, timestamp_bucket, result_json) VALUES (?, ?, ?)",
        (video_id, bucket, result_json)
    )
    conn.commit()


def save_lookup(conn: sqlite3.Connection, lookup: dict):
    conn.execute(
        """INSERT INTO lookups (id, user_id, video_id, timestamp_seconds,
           location_name, region, country, lat, lon, confidence,
           evidence_json, maps_url, status)
           VALUES (:id, :user_id, :video_id, :timestamp_seconds,
           :location_name, :region, :country, :lat, :lon, :confidence,
           :evidence_json, :maps_url, :status)""",
        lookup
    )
    conn.commit()


def get_user_history(conn: sqlite3.Connection, user_id: str, limit: int = 50):
    rows = conn.execute(
        """SELECT id, video_id, timestamp_seconds, location_name, country,
           confidence, maps_url, created_at
           FROM lookups WHERE user_id = ? ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    return [dict(r) for r in rows]


def save_feedback(conn: sqlite3.Connection, lookup_id: str, user_id: str, vote: str, correct_location: str | None):
    conn.execute(
        "INSERT INTO feedback (lookup_id, user_id, vote, correct_location) VALUES (?, ?, ?, ?)",
        (lookup_id, user_id, vote, correct_location)
    )
    conn.commit()
