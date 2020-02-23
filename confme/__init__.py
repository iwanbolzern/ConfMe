from dataclasses import dataclass
from typing import get_type_hints, Dict

from file_backend import file_backend
from parsing import root_parser


def configclass(_cls):
    _cls.__config_class__ = True
    return dataclass(_cls)


def is_config_class(cls):
    if not getattr(cls, '__dict__', None):
        return False

    return '__config_class__' in cls.__dict__


def load_config(config_class, path: str):
    config_content = file_backend.parse_file(path)

    return fill_config_classes(config_class, config_content)


def fill_config_classes(config_type_head, yaml_head: Dict):
    params = {}
    for attr_name, attr_type in get_type_hints(config_type_head).items():
        if is_config_class(attr_type):
            params[attr_name] = fill_config_classes(attr_type, yaml_head[attr_name])
        else:
            params[attr_name] = root_parser.parse(attr_name, attr_type, yaml_head.get(attr_name, None))

    return config_type_head(**params)