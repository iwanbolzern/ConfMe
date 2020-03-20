"""ConfigurationMadeEasy package exports"""

from pydantic import BaseSettings

from confme import source_backend


class BaseConfig(BaseSettings):

    @classmethod
    def load(cls, path: str) -> 'BaseConfig':
        """Load your configuration file into your config class structure.
        :param config_class: Root class to map the configuration file to
        :param path: path to configuration file
        :return: instance of config_class with all values added from the config file
        """
        config_content = source_backend.parse_file(path)
        from confme.argument_overwrite import overwrite_config
        overwrite_config(cls)

        return cls.parse_obj(config_content)
