"""ConfigurationMadeEasy package exports"""
import argparse
import logging
import os
from pathlib import Path
from typing import Any, Tuple, List, Dict, Union, TypeVar

from confme import source_backend
from confme.utils.base_exception import ConfmeException
from confme.utils.dict_util import flatten, InfiniteDict, recursive_update
from confme.utils.typing import get_schema
from pydantic import BaseSettings


def argument_overwrite(config_cls):
    # extract possible parameters
    config_dict = get_schema(config_cls)
    parameters, _ = flatten(config_dict)

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
    def load(cls, path: Union[Path, str]) -> 'BaseConfig':
        """Load your configuration file into your config class structure.
        :param config_class: Root class to map the configuration file to
        :param path: path to configuration file
        :return: instance of config_class with all values added from the config file
        """
        config_content = source_backend.parse_file(Path(path))
        config_content = recursive_update(config_content, argument_overwrite(cls))

        return cls.parse_obj(config_content)

    def update_by_str(self, path: str, value: Any):
        """Given a path string separated by dots (.) this method allows to update nested configuration objects.
        CAVEAT: For this update no type check is applied!
        e.g. given this configuration
        ```
        class DatabaseConfig(BaseConfig):
            host: str
            port: int
            user: str

        class MyConfig(BaseConfig):
            name: int
            database: DatabaseConfig

        config = MyConfig.load('test.yaml')

        config.update_by_str('database.host', 'my new host')
        :param path: dot (.) separated string which value should be updated
        :param value: update value
        """
        path = path.split('.')
        current = self
        for i, segment in enumerate(path):
            if not hasattr(current, segment):
                raise ConfmeException(f'{segment} not found in path {".".join(path[:i])}!')

            # for the last item we don't want to assign it to the current element because we want to assign the given
            # value instead
            if i + 1 < len(path):
                current = getattr(current, segment)
            else:
                setattr(current, segment, value)

    def get_flat_repr(self) -> List[Tuple[str, Any]]:
        """Returns a flat representation of your configuration structure (tree).
        e.g. given this configuration
        ```
        class DatabaseConfig(BaseConfig):
            host: str
            port: int
            user: str

        class MyConfig(BaseConfig):
            name: int
            database: DatabaseConfig

        config = MyConfig.load('test.yaml')
        config.get_flat_repr()
        ...
        [('name', 'test1'),
        ('database.host', 'localhost'),
        ('database.port', '5678'),
        ('database.user', 'db_user')]

        :return: list of configuration parameter key and it's corresponding value
        """
        keys, values = flatten(self.dict())
        return list(zip(keys, values))


T = TypeVar('T', bound=BaseConfig)


class GlobalConfig(BaseConfig):
    _KEY_LOOKUP = ['env', 'environment', 'environ', 'stage']
    _config_path: Path = None
    _cache: Dict[str, T] = {}

    @classmethod
    def register_folder(cls, config_folder: Path):
        cls._config_path = config_folder

    @classmethod
    def get(cls) -> T:
        env = cls._get_current_env()
        if env not in cls._cache:
            cls._cache[env] = cls._load_file(env)

        return cls._cache[env]

    @classmethod
    def _load_file(cls, environment: str) -> T:
        files = Path(cls._config_path).glob(pattern='*')
        selected_files = [f for f in files if environment in f.name]

        if len(selected_files) <= 0:
            raise Exception(f'No configuration found for environment {environment} in '
                            f'files {files}')
        elif len(selected_files) > 1:
            logging.warning(f'More than one file found matching environment {environment} in'
                            f'files {files}. Using file {selected_files[0]}')
            file = selected_files[0]
        else:
            file = selected_files[0]

        return cls.load(file)

    @classmethod
    def _get_current_env(cls) -> str:
        keys = [key for key in os.environ.keys() if key.lower() in cls._KEY_LOOKUP]

        if len(keys) <= 0:
            raise Exception(f"You're using the register_folder / get combination one of the "
                            f"following environment variables need to be set: ENV, ENVIRONMENT,"
                            f"ENVIRON, env, environment, environ")
        elif len(keys) > 1:
            logging.warning(f'More than one environment variable set using the value of {keys[0]}')
            key = keys[0]
        else:
            key = keys[0]

        return os.environ[key].lower()

