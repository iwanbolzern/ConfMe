from confme import BaseConfig
from os import path

class DatabaseConfig(BaseConfig):
    host: str
    port: int
    user: str


class MyConfig(BaseConfig):
    name: str
    database: DatabaseConfig


dir_path = path.dirname(path.realpath(__file__))

config = MyConfig.load(path.join(dir_path, 'test_config.yaml'))
print(config)


