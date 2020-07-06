"""ConfigurationMadeEasy package exports"""
import argparse

from pydantic import BaseSettings

from confme import source_backend
from confme.utils.typing import get_schema
from confme.utils.dict_util import flatten, InfiniteDict, recursive_update


def argument_overwrite(config_cls):
    # extract possible parameters
    config_dict = get_schema(config_cls)
    parameters = flatten(config_dict)

    # get arguments from command line
    parser = argparse.ArgumentParser()
    group = parser.add_argument_group('Configuration Parameters',
                                      'With the parameters specified bellow, '
                                      'the configuration values from the config file can be overwritten.')
    for param in parameters:
        group.add_argument(f'--{param}', required=False)
    args, unknown = parser.parse_known_args()

    # find passed arguments and fill it into the dict structure
    infinite_dict = InfiniteDict()
    for param in parameters:
        value = getattr(args, param)
        if value:
            infinite_dict.expand(param.split('.'), value)

    return infinite_dict


class BaseConfig(BaseSettings):

    @classmethod
    def load(cls, path: str) -> 'BaseConfig':
        """Load your configuration file into your config class structure.
        :param config_class: Root class to map the configuration file to
        :param path: path to configuration file
        :return: instance of config_class with all values added from the config file
        """
        config_content = source_backend.parse_file(path)
        config_content = recursive_update(config_content, argument_overwrite(cls))

        return cls.parse_obj(config_content)
