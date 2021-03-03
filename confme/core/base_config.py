from pathlib import Path
from typing import Union, Any, List, Tuple

from pydantic import BaseSettings

from confme import source_backend
from confme.core.argument_overwrite import argument_overwrite
from confme.utils.base_exception import ConfmeException
from confme.utils.dict_util import recursive_update, flatten


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
