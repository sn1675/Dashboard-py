import sqlite3
from ast import Dict
from pathlib import Path

def get_connection(config: Dict) -> sqlite3.Connection:
    db_path = config["database"]["path"]
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(config: Dict):
    conn = get_connection(config)
    cursor = conn.cursor()

    cursor.execute("""
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

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_ip ON requests(ip)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON requests(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            type        TEXT NOT NULL,
            ip          TEXT NOT NULL,
            detail      TEXT,
            resolved    INTEGER DEFAULT 0
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ip ON alerts(ip)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type)")

    # IPs bannies / flaggées
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_ips (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ip          TEXT UNIQUE NOT NULL,
            reason      TEXT,
            banned_at   TEXT NOT NULL,
            expires_at  TEXT         
        )
    """)

    conn.commit()
    conn.close()
    print("[*] Base de données initialisée")

def insert_requests(config: dict, requests: list[dict]):
    if not requests:
        return
    conn = get_connection(config)
    cursor = conn.cursor()
    cursor.executemany("""
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
    conn.commit()
    conn.close()


def insert_alert(config: dict, alert_type: str, ip: str, detail: str, timestamp: str):
    conn = get_connection(config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alerts (timestamp, type, ip, detail)
        VALUES (?, ?, ?, ?)
    """, (timestamp, alert_type, ip, detail))
    conn.commit()
    conn.close()