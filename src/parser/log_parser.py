import re
from datetime import datetime
from pathlib import Path
from typing import Optional


# Regex pour le Combined Log Format d'Apache
LOG_PATTERN = re.compile(
    r'(?P<ip>\S+)'          # IP source
    r' \S+ \S+ '            # ident et user (souvent "- -")
    r'\[(?P<timestamp>[^\]]+)\] '  # timestamp entre crochets
    r'"(?P<method>\S+) '    # méthode HTTP
    r'(?P<path>\S+) '       # chemin
    r'\S+" '                # protocole
    r'(?P<status>\d{3}) '   # status code
    r'(?P<size>\S+)'        # taille réponse (peut être "-")
    r'(?: "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)")?'  # referrer + UA (optionnels)
)

TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def parse_line(line: str) -> Optional[dict]:
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None

    data = match.groupdict()

    try:
        data["timestamp"] = datetime.strptime(data["timestamp"], TIMESTAMP_FORMAT)
    except ValueError:
        return None

    data["status"] = int(data["status"])
    data["size"] = int(data["size"]) if data["size"] != "-" else 0

    return data


def tail_log(filepath: str, last_position: int = 0) -> tuple[list[dict], int]:
    path = Path(filepath)
    if not path.exists():
        return [], last_position

    requests = []

    with open(filepath, "r") as f:
        f.seek(last_position)
        for line in f:
            parsed = parse_line(line)
            if parsed:
                requests.append(parsed)
        new_position = f.tell()

    return requests, new_position