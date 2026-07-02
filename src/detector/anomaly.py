from collections import defaultdict
from datetime import datetime


def detect(requests: list[dict], config: dict) -> list[dict]:
    alerts = []
    detection_cfg = config["detection"]

    ddos_threshold = detection_cfg["ddos_threshold"]
    scan_threshold = detection_cfg["scan_threshold"]
    suspicious_paths = detection_cfg["suspicious_paths"]

    requests_per_ip = defaultdict(int)
    not_found_per_ip = defaultdict(int)

    for req in requests:
        ip = req["ip"]
        path = req.get("path", "")
        status = req.get("status", 0)
        timestamp = req.get("timestamp", datetime.now()).isoformat()

        requests_per_ip[ip] += 1

        if status == 404:
            not_found_per_ip[ip] += 1

        for suspicious in suspicious_paths:
            if suspicious.lower() in path.lower():
                alerts.append({
                    "type": "suspicious_path",
                    "ip": ip,
                    "detail": f"Accès à un chemin sensible : {path}",
                    "timestamp": timestamp,
                })
                break

    now = datetime.now().isoformat()

    for ip, count in requests_per_ip.items():
        if count >= ddos_threshold:
            alerts.append({
                "type": "ddos",
                "ip": ip,
                "detail": f"{count} requêtes en un seul cycle de lecture",
                "timestamp": now,
            })

    for ip, count in not_found_per_ip.items():
        if count >= scan_threshold:
            alerts.append({
                "type": "scan",
                "ip": ip,
                "detail": f"{count} erreurs 404 consécutives (scan probable)",
                "timestamp": now,
            })

    return alerts