import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager

_lock = threading.Lock()
_db_path: str | None = None


@contextmanager
def get_db(config: dict):
    global _db_path
    if _db_path is None:
        _db_path = config["database"]["path"]
        Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

    with _lock:
        conn = sqlite3.connect(_db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db(config: dict):
    with get_db(config) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ip          TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                method      TEXT,
                path        TEXT,
                status      INTEGER,
                size        INTEGER,
                referrer    TEXT,
                user_agent  TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_ip ON requests(ip)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON requests(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                type        TEXT NOT NULL,
                ip          TEXT NOT NULL,
                detail      TEXT,
                resolved    INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ip ON alerts(ip)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS banned_ips (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ip          TEXT UNIQUE NOT NULL,
                reason      TEXT,
                banned_at   TEXT NOT NULL,
                expires_at  TEXT
            )
        """)
    print("[*] Base de données initialisée")


def insert_requests(config: dict, requests: list[dict]):
    if not requests:
        return
    with get_db(config) as conn:
        conn.executemany("""
            INSERT INTO requests (ip, timestamp, method, path, status, size, referrer, user_agent)
            VALUES (:ip, :timestamp, :method, :path, :status, :size, :referrer, :user_agent)
        """, [
            {
                "ip": r["ip"],
                "timestamp": r["timestamp"].isoformat(),
                "method": r.get("method"),
                "path": r.get("path"),
                "status": r.get("status"),
                "size": r.get("size", 0),
                "referrer": r.get("referrer"),
                "user_agent": r.get("user_agent"),
            }
            for r in requests
        ])


def insert_alert(config: dict, alert_type: str, ip: str, detail: str, timestamp: str):
    with get_db(config) as conn:
        conn.execute("""
            INSERT INTO alerts (timestamp, type, ip, detail)
            VALUES (?, ?, ?, ?)
        """, (timestamp, alert_type, ip, detail))