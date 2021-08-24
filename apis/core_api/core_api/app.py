import argparse
from pathlib import Path

import yaml

from core_api.server import app

if __name__ == "__main__":
    with open(Path(__file__).resolve().parent / "api_config.yaml") as f:
        config = yaml.safe_load(f)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--port",
        type=int,
        help="Port number (default: port number from the config file.",
        default=config["port"],
    )
    args = parser.parse_args()

    app.run(threaded=False, host="0.0.0.0", processes=config["n_procs"], port=args.port)
