import os
import uuid
from pathlib import Path

import pytest

from tests.unit.config_model import GlobalRootConfig, RootConfig


@pytest.fixture
def test_config_yaml(tmp_path: str):
    config_content = 'rootValue: 1\n' \
                     'rangeValue: 5\n' \
                     'childNode:\n' \
                     '  testStr: "test-env"\n' \
                     '  testInt: 42\n' \
                     '  testFloat: 42.42\n' \
                     '  anyEnum: value2'

    config_path = Path(tmp_path) / f'{uuid.uuid4()}_test.yaml'
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)

    return str(config_path)


@pytest.fixture
def prod_config_yaml(tmp_path: str):
    config_content = 'rootValue: 1\n' \
                     'rangeValue: 5\n' \
                     'childNode:\n' \
                     '  testStr: "prod-env"\n' \
                     '  testInt: 42\n' \
                     '  testFloat: 42.42\n' \
                     '  anyEnum: value2'

    config_path = Path(tmp_path) / f'{uuid.uuid4()}_prod.yaml'
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)

    return str(config_path)


def test_load_global_config(prod_config_yaml: str, test_config_yaml: str):
    os.environ['highSecure'] = 'superSecureSecret'

    GlobalRootConfig.register_folder(Path(prod_config_yaml).parent)

    os.environ['ENV'] = 'test'
    root_config = GlobalRootConfig.get()
    assert root_config.childNode.testStr == 'test-env'

    os.environ['ENV'] = 'prod'
    root_config = GlobalRootConfig.get()
    assert root_config.childNode.testStr == 'prod-env'


def test_load_config_by_env(prod_config_yaml: str, test_config_yaml: str):
    os.environ['highSecure'] = 'superSecureSecret'

    RootConfig.register_folder(Path(prod_config_yaml).parent)

    os.environ['ENV'] = 'test'
    root_config = RootConfig.get()
    assert root_config.childNode.testStr == 'test-env'

    os.environ['ENV'] = 'prod'
    root_config = RootConfig.get()
    assert root_config.childNode.testStr == 'prod-env'
