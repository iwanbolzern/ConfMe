import argparse
from collections import defaultdict, MutableMapping

from confme import BaseConfig


def create_dict(head):
    config_structure = {}
    for key, value in head.__fields__.items():
        if issubclass(value.type_, BaseConfig):
            config_structure[key] = create_dict(value.type_)
        else:
            config_structure[key] = None

    return config_structure


def flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep))
        else:
            items.append(new_key)
    return items


class InfiniteDict(defaultdict):
    def __init__(self):
        defaultdict.__init__(self, self.__class__)

def update(infinite_dict, levels, value):
    if len(levels) <= 0:
        return value

    return update(infinite_dict[levels[0]], levels[1:], value)


def overwrite_config(config_cls):
    config_dict = create_dict(config_cls)
    parameters = flatten(config_dict)
    parser = argparse.ArgumentParser()
    for param in parameters:
        parser.add_argument(f'--{param}', required=False)
    args, unknown = parser.parse_known_args()
    infinite_dict = InfiniteDict()
    for param in parameters:
        value = getattr(args, parameters[0])
        if value:
            update(infinite_dict, param.split('.'), value)

    return infinite_dict
