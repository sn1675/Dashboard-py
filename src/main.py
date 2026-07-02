import uvicorn
import yaml
from pathlib import Path

def load_config(path: str = "config/config.yaml") -> dict:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()

    from database.db import init_db
    from api.routes import create_app

    init_db(config)

    app = create_app(config)

    print(f"[*] Dashboard démarré sur http://{config['server']['host']}:{config['server']['port']}")
    print(f"[*] Lecture des logs : {config['apache']['access_log']}")

    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
    )


if __name__ == "__main__":
    main()