import logging
import os
from pathlib import Path
from typing import Any, Callable, ClassVar, Self

from pydantic import BaseModel
from tabulate import tabulate

from confme import source_backend
from confme.core.argument_overwrite import argument_overwrite
from confme.core.env_overwrite import env_overwrite
from confme.utils.base_exception import ConfmeException
from confme.utils.dict_util import flatten, recursive_update


class BaseConfig(BaseModel):
    __KEY_LOOKUP__: ClassVar[list[str]] = ["env", "environment", "environ", "stage"]
    __config_path__: ClassVar[Path | None] = None
    __default_env__: ClassVar[str | None] = None
    __cache__: ClassVar[dict[str, "BaseConfig"]] = {}

    @classmethod
    def load(cls, path: Path | str) -> Self:
        """Load your configuration file into your config class structure.
        :param config_class: Root class to map the configuration file to
        :param path: path to configuration file
        :return: instance of config_class with all values added from the config file
        """
        config_content = source_backend.parse_file(path)
        config_content = recursive_update(config_content, env_overwrite(cls))
        config_content = recursive_update(config_content, argument_overwrite(cls))

        return cls.model_validate(config_content)

    @classmethod
    def load_from_dict(cls, config_content: dict[str, Any]) -> Self:
        config_content = recursive_update(config_content, env_overwrite(cls))
        config_content = recursive_update(config_content, argument_overwrite(cls))

        return cls.model_validate(config_content)

    @classmethod
    def register_folder(
        cls,
        config_folder: Path,
        default_env: str | None = None,
        strict: bool = False,
    ) -> None:
        """Register a folder where configuration files are drawn based on the environment.
        :param config_folder: Path to the folder with configuration files per environment
        :param default_env: Default environment that should be used if none is specified via environment variable
        :param strict: If True, an exception is raised if no configuration file is found that exactly matches env name.
        """
        cls.__config_path__ = config_folder
        cls.__default_env__ = default_env
        cls._strict = strict
        cls.__cache__ = {}

    @classmethod
    def get(cls) -> Self:
        """Get the corresponding configuration based on the environment. Thereby, the configuration class is loaded
        once and cached for subsequent calls.
        :return: instance of config_class with all values added from the config file
        """
        env = cls._get_current_env()
        if env not in cls.__cache__:
            cls.__cache__[env] = cls._load_file(env)

        return cls.__cache__[env]  # type: ignore[return-value]

    @classmethod
    def _load_file(cls, environment: str) -> Self:
        if cls.__config_path__ is None:
            raise ConfmeException("Config path not set. Call register_folder() first.")
        files = list(cls.__config_path__.glob(pattern="*"))
        if cls._strict:
            selected_files = [f for f in files if f.name == environment or f.stem == environment]
        else:
            selected_files = [f for f in files if environment in f.name]

        if len(selected_files) <= 0:
            raise ConfmeException(f"No configuration found for environment {environment} in files {files}")
        elif len(selected_files) > 1:
            logging.warning(
                f"More than one file found matching environment {environment} in"
                f"files {files}. Using file {selected_files[0]}"
            )
            file = selected_files[0]
        else:
            file = selected_files[0]

        return cls.load(file)

    @classmethod
    def _get_current_env(cls) -> str:
        keys = [key for key in os.environ.keys() if key.lower() in cls.__KEY_LOOKUP__]

        if len(keys) <= 0 and cls.__default_env__ is None:
            raise Exception(
                "You're using the register_folder / get combination one of the "
                "following environment variables need to be set: ENV, ENVIRONMENT,"
                "ENVIRON, env, environment, environ"
            )
        elif len(keys) <= 0 and cls.__default_env__ is not None:
            return cls.__default_env__
        elif len(keys) > 1:
            logging.warning(f"More than one environment variable set using the value of {keys[0]}")
            key = keys[0]
        else:
            key = keys[0]

        return os.environ[key].lower()

    def update_by_str(self, path: str, value: Any) -> None:
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
        path_parts = path.split(".")
        current = self
        for i, segment in enumerate(path_parts):
            if not hasattr(current, segment):
                raise ConfmeException(f"{segment} not found in path {'.'.join(path_parts[:i])}!")

            # for the last item we don't want to assign it to the current element because we want to assign the given
            # value instead
            if i + 1 < len(path_parts):
                current = getattr(current, segment)
            else:
                setattr(current, segment, value)

    def get_flat_repr(self) -> list[tuple[str, Any]]:
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
        keys, values = flatten(self.model_dump())
        return list(zip(keys, values))

    def log_config(self, print_fn: Callable[[str], None] = logging.info):
        """Prints/logs the configuration in a flat format.
        :param print_fn: print callable to overwrite can be used e.g. with log_config(print_fn=print)
        """
        flat_config = self.get_flat_repr()
        str_config = tabulate(flat_config, headers=["Key", "Value"], tablefmt="github")
        print_fn(str_config)
