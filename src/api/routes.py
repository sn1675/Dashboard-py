import threading
import time
import os
from datetime import datetime

import bcrypt
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

from parser.log_parser import tail_log
from detector.anomaly import detect
from database.db import insert_requests, insert_alert, get_db


security = HTTPBasic()

load_dotenv()


def create_app(config: dict) -> FastAPI:
    app = FastAPI(title="Apache Dashboard")

    password_hash = os.environ.get("DASHBOARD_PASSWORD_HASH")
    secret_key = os.environ.get("DASHBOARD_SECRET_KEY")

    if not password_hash or not secret_key:
        raise RuntimeError(
            "DASHBOARD_PASSWORD_HASH et DASHBOARD_SECRET_KEY doivent être définis dans .env\n"
            "Lance d'abord : python generate_password_hash.py"
        )

    def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
        valid_user = secrets.compare_digest(credentials.username, config["auth"]["username"])
        valid_pass = bcrypt.checkpw(
            credentials.password.encode(),
            password_hash.encode()
        )
        if not (valid_user and valid_pass):
            raise HTTPException(status_code=401, detail="Accès refusé")
        return credentials.username

    file_position = {"value": 0}

    def polling_loop():
        while True:
            requests, file_position["value"] = tail_log(
                config["apache"]["access_log"],
                file_position["value"]
            )
            if requests:
                insert_requests(config, requests)
                alerts = detect(requests, config)
                for alert in alerts:
                    insert_alert(
                        config,
                        alert["type"],
                        alert["ip"],
                        alert["detail"],
                        alert["timestamp"],
                    )
            time.sleep(config["apache"]["poll_interval"])

    thread = threading.Thread(target=polling_loop, daemon=True)
    thread.start()
    print(f"[*] Polling démarré (intervalle : {config['apache']['poll_interval']}s)")

    # --- Routes API ---

    @app.get("/api/stats")
    def get_stats(username: str = Depends(check_auth)):
        with get_db(config) as conn:
            total = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
            top_ips = conn.execute("""
                SELECT ip, COUNT(*) as count FROM requests
                GROUP BY ip ORDER BY count DESC LIMIT 10
            """).fetchall()
            status_dist = conn.execute("""
                SELECT status, COUNT(*) as count FROM requests
                GROUP BY status ORDER BY count DESC
            """).fetchall()
            requests_over_time = conn.execute("""
                SELECT strftime('%Y-%m-%dT%H:00:00', timestamp) as hour, COUNT(*) as count
                FROM requests GROUP BY hour ORDER BY hour DESC LIMIT 24
            """).fetchall()
        return {
            "total_requests": total,
            "top_ips": [{"ip": r["ip"], "count": r["count"]} for r in top_ips],
            "status_distribution": [{"status": r["status"], "count": r["count"]} for r in status_dist],
            "requests_over_time": [{"hour": r["hour"], "count": r["count"]} for r in requests_over_time],
        }

    @app.get("/api/alerts")
    def get_alerts(limit: int = 50, username: str = Depends(check_auth)):
        with get_db(config) as conn:
            rows = conn.execute(
                "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    @app.get("/api/requests/recent")
    def get_recent_requests(limit: int = 100, username: str = Depends(check_auth)):
        with get_db(config) as conn:
            rows = conn.execute(
                "SELECT * FROM requests ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    @app.get("/api/requests/suspicious")
    def get_suspicious_requests(username: str = Depends(check_auth)):
        suspicious = config["detection"]["suspicious_paths"]
        placeholders = " OR ".join(["path LIKE ?" for _ in suspicious])
        params = [f"%{p}%" for p in suspicious]
        with get_db(config) as conn:
            rows = conn.execute(f"""
                SELECT * FROM requests WHERE {placeholders}
                ORDER BY timestamp DESC LIMIT 200
            """, params).fetchall()
        return [dict(r) for r in rows]

    # Sert le frontend statique
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

    return app