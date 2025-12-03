# imports
import json

from typing import Union


def get_config(path: str = "etc/conf.json") -> dict:
    with open(path, "r") as fp:
        return json.load(fp)


def set_config(new_config: dict) -> int:
    with open("etc/conf.json", "w") as fp:
        return fp.write(json.dumps(new_config))
