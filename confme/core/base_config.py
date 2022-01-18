import logging
import os
from pathlib import Path
from typing import Union, Any, List, Tuple, Callable, TypeVar, Dict

from pydantic import BaseSettings
from tabulate import tabulate

from confme import source_backend
from confme.core.argument_overwrite import argument_overwrite
from confme.core.env_overwrite import env_overwrite
from confme.utils.base_exception import ConfmeException
from confme.utils.dict_util import recursive_update, flatten

T = TypeVar('T', bound='BaseConfig')


class BaseConfig(BaseSettings):
    _KEY_LOOKUP = ['env', 'environment', 'environ', 'stage']
    _config_path: Path = None
    _cache: Dict[str, T] = {}

    @classmethod
    def load(cls, path: Union[Path, str]) -> 'BaseConfig':
        """Load your configuration file into your config class structure.
        :param config_class: Root class to map the configuration file to
        :param path: path to configuration file
        :return: instance of config_class with all values added from the config file
        """
        config_content = source_backend.parse_file(Path(path))
        config_content = recursive_update(config_content, env_overwrite(cls))
        config_content = recursive_update(config_content, argument_overwrite(cls))

        return cls.parse_obj(config_content)

    @classmethod
    def load_from_dict(cls, config_content: Dict) -> 'BaseConfig':
        config_content = recursive_update(config_content, env_overwrite(cls))
        config_content = recursive_update(config_content, argument_overwrite(cls))

        return cls.parse_obj(config_content)

    @classmethod
    def register_folder(cls, config_folder: Path):
        """Register a folder where configuration files are drawn based on the environment.
        :param config_folder: Path to the folder with configuration files per environment
        """
        cls._config_path = config_folder
        cls._cache = {}

    @classmethod
    def get(cls) -> T:
        """Get the corresponding configuration based on the environment. Thereby, the configuration class is loaded
        once and cached for subsequent calls.
        :return: instance of config_class with all values added from the config file
        """
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

    def log_config(self, print_fn: Callable[[str], None] = logging.info):
        """Prints/logs the configuration in a flat format.
        :param print_fn: print callable to overwrite can be used e.g. with log_config(print_fn=print)
        """
        flat_config = self.get_flat_repr()
        str_config = tabulate(flat_config, headers=['Key', 'Value'], tablefmt="github")
        print_fn(str_config)
