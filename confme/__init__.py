"""ConfigurationMadeEasy package exports"""
from dataclasses import dataclass
from typing import get_type_hints, Dict, Any

from confme.source_backend import file_backend
from confme.parsing import root_parser


def configclass(_cls: Any) -> Any:
    """Class annotation to mark a class as configclass and use it as config holder.
    :param _cls: class type to mark as configclass
    :return: marked class type
    """
    _cls.__config_class__ = True
    return dataclass(_cls)


def _is_config_class(cls):
    if not getattr(cls, '__dict__', None):
        return False

    return '__config_class__' in cls.__dict__


def load_config(config_class: Any, path: str) -> Any:
    """Load your configuration file into your config class structure.
    :param config_class: Root class to map the configuration file to
    :param path: path to configuration file
    :return: instance of config_class with all values added from the config file
    """
    config_content = file_backend.parse_file(path)

    return _fill_config_classes(config_class, config_content)


def _fill_config_classes(config_type_head: Any, yaml_head: Dict) -> Any:
    params = {}
    for attr_name, attr_type in get_type_hints(config_type_head).items():
        if _is_config_class(attr_type):
            params[attr_name] = _fill_config_classes(attr_type, yaml_head[attr_name])
        else:
            params[attr_name] = root_parser.parse(attr_name, attr_type, yaml_head.get(attr_name, None))

    return config_type_head(**params)
