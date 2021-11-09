import os
import subprocess
import sys

import pathlib


os.environ['ENSEMBLE_CONFIG_PATH'] = "/mnt/mantle_data/seistech/ensemble_configs"

command = ["python3", pathlib.Path(__file__).parent.resolve() / "baseline.py"]
subprocess.check_call(command)