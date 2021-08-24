import os

import yaml

from project_api import app

if __name__ == "__main__":
    with open(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "api_config.yaml")
    ) as f:
        config = yaml.safe_load(f)

    app.run(
        threaded=False, host="0.0.0.0", processes=config["n_procs"], port=config["port"]
    )
