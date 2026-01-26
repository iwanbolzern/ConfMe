import os

from pydantic import BaseModel

from confme.utils.dict_util import InfiniteDict, flatten
from confme.utils.typing import get_schema


def env_overwrite(config_cls: type[BaseModel]) -> InfiniteDict:
    # extract possible parameters
    config_dict = get_schema(config_cls)
    parameters: list[str] = []
    if config_dict is not None:
        parameters, _ = flatten(config_dict)

    # make env variables case insensitive
    keys, values = zip(*os.environ.items())
    keys = [k.casefold() for k in keys]

    # find passed arguments and fill it into the dict structure
    infinite_dict = InfiniteDict()
    for p in parameters:
        if p.casefold() in keys:
            i = keys.index(p.casefold())
            infinite_dict.expand(p.split("."), values[i])

    return infinite_dict
