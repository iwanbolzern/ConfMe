import sys

from confme import BaseConfig


class DatabaseConfig(BaseConfig):
    host: str
    port: int
    user: str


class MyConfig(BaseConfig):
    name: str
    database: DatabaseConfig


config = MyConfig.load('test_config.yaml')
print(config)


