# db.py
import sqlite3
import threading
from datetime import datetime, timezone
import os

DB_FILE = 'aura_data.db'
_lock = threading.Lock()

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            due_ts INTEGER,  -- epoch seconds UTC
            notified INTEGER DEFAULT 0
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            text TEXT,
            ts INTEGER
        )""")
        conn.commit()
        conn.close()

def save_memory_key(key, value):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO user_memory(key, value, updated_at) VALUES (?, ?, ?)",
                    (key, str(value), int(datetime.now().timestamp())))
        conn.commit()
        conn.close()

def load_memory_all():
    d = {}
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM user_memory")
        for row in cur.fetchall():
            d[row['key']] = row['value']
        conn.close()
    return d

def add_reminder(message, due_ts):
    """due_ts = epoch seconds UTC"""
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO reminders(message, due_ts, notified) VALUES (?, ?, 0)", (message, int(due_ts)))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
    return rid

def get_due_reminders(now_ts=None):
    if now_ts is None:
        now_ts = int(datetime.now().timestamp())
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, message, due_ts FROM reminders WHERE notified=0 AND due_ts <= ?", (int(now_ts),))
        rows = cur.fetchall()
        conn.close()
    return rows

def mark_reminder_notified(reminder_id):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE reminders SET notified=1 WHERE id=?", (reminder_id,))
        conn.commit()
        conn.close()

def log_chat(role, text):
    ts = int(datetime.now().timestamp())
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO chat_log(role, text, ts) VALUES (?, ?, ?)", (role, text, ts))
        conn.commit()
        conn.close()
