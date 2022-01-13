import argparse

from pydantic.main import ModelMetaclass

from confme.utils.dict_util import flatten, InfiniteDict
from confme.utils.typing import get_schema


def argument_overwrite(config_cls: ModelMetaclass):
    # extract possible parameters
    config_dict = get_schema(config_cls)
    parameters, _ = flatten(config_dict)

    # get arguments from command line
    parser = argparse.ArgumentParser(prefix_chars='+/')
    group = parser.add_argument_group('Configuration Parameters',
                                      'With the parameters specified bellow, '
                                      'the configuration values from the config file can be overwritten.')
    for param in parameters:
        group.add_argument(f'++{param}', required=False)
    args, unknown = parser.parse_known_args()

    # find passed arguments and fill it into the dict structure
    infinite_dict = InfiniteDict()
    for param in parameters:
        value = getattr(args, param)
        if value:
            infinite_dict.expand(param.split('.'), value)

    return infinite_dict
