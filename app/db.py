import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def read_json(filename: str) -> list | dict:
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r") as f:
        return json.load(f)


def write_json(filename: str, data: list | dict):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
