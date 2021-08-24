from pathlib import Path

import yaml
import pytest


@pytest.fixture
def config():
    """ Loads the config yaml file for all of the core API tests"""
    with open(Path(__file__).resolve().parent / "config.yaml") as f:
        config = yaml.safe_load(f)

    return config
