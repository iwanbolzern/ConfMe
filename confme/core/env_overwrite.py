import os

from pydantic.main import ModelMetaclass

from confme.utils.dict_util import flatten, InfiniteDict
from confme.utils.typing import get_schema


def env_overwrite(config_cls: ModelMetaclass):
    # extract possible parameters
    config_dict = get_schema(config_cls)
    parameters, _ = flatten(config_dict)

    # make case insensitive
    original = [(p_org, p_org) for p_org in parameters]
    lower = [(p_org.lower(), p_org) for p_org in parameters]
    upper = [(p_org.upper(), p_org) for p_org in parameters]
    parameters = original + lower + upper

    # find passed arguments and fill it into the dict structure
    infinite_dict = InfiniteDict()
    for p, p_org in parameters:
        if p in os.environ:
            value = os.environ[p]
            infinite_dict.expand(p_org.split('.'), value)

    return infinite_dict
