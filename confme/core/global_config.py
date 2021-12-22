import logging
import os
from pathlib import Path
from typing import Dict, TypeVar

from confme import BaseConfig

T = TypeVar('T', bound='BaseConfig')


class GlobalConfig(BaseConfig):
    _KEY_LOOKUP = ['env', 'environment', 'environ', 'stage']
    _config_path: Path = None
    _cache: Dict[str, T] = {}

    @classmethod
    def register_folder(cls, config_folder: Path):
        cls._config_path = config_folder
        cls._cache = {}

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
