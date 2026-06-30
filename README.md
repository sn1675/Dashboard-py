# Dashboard-py

Dashboard for visualizing Apache server traffic.

> [!IMPORTANT]
> This project is still in development. Avoid using it in production.

## Context

This project aims to help manage a personal web server, providing visibility into traffic and basic security monitoring through several core features:

- Log visualizer
- Notifier for abnormal traffic
- Data analysis

## Features

- Real-time parsing of Apache access logs
- SQLite-backed storage of requests and security alerts
- Detection rules for suspicious activity (DDoS-like bursts, directory scans, access to sensitive paths)
- REST API for consuming traffic data and alerts
- Lightweight web dashboard, served alongside the API

## Requirements

- Linux (Arch, Debian, Ubuntu, Fedora, ...)
- Apache web server (any version)
- Python 3.10+

As the project is still in development, additional requirements may be introduced in the future.

## Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/sn1675/Dashboard-py
cd Dashboard-py
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and fill in the required secrets:

```bash
cp .envExample .env
```

Generate a password hash:

```bash
python generate_password_hash.py
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste both values into `.env`.

General settings (log paths, detection thresholds, server port, etc.) are configured in `config.yaml`.

### Running

```bash
python main.py
```

The dashboard will be available at `http://localhost:8443` (or the port configured in `config.yaml`).

## Project Structure

```
Dashboard-py/
├── config.yaml
├── main.py
├── requirements.txt
├── src/
│   ├── parser/      # Apache log parsing
│   ├── detector/     # Anomaly detection rules
│   ├── database/      # SQLite access layer
│   ├── api/         # FastAPI routes
│   └── alerts/       # Notification logic
├── frontend/        # Static dashboard UI
└── tests/
```

## License

This project is open source.
