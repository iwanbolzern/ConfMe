import os
import uuid
from pathlib import Path

import pytest

from confme import ConfmeException
from tests.unit.config_model import RootConfig


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


def test_load_config_by_env(prod_config_yaml: str, test_config_yaml: str):
    os.environ['highSecure'] = 'superSecureSecret'

    RootConfig.register_folder(Path(prod_config_yaml).parent, default_env='prod')

    root_config = RootConfig.get()
    assert root_config.childNode.testStr == 'prod-env'

    os.environ['ENV'] = 'test'
    root_config = RootConfig.get()
    assert root_config.childNode.testStr == 'test-env'

    os.environ['ENV'] = 'prod'
    root_config = RootConfig.get()
    assert root_config.childNode.testStr == 'prod-env'


def test_load_config_by_env_strict(prod_config_yaml: str, test_config_yaml: str):
    os.environ['highSecure'] = 'superSecureSecret'
    prod_exact_name = Path(prod_config_yaml).name
    test_exact_name = Path(test_config_yaml).name

    RootConfig.register_folder(Path(prod_config_yaml).parent, default_env='prod', strict=True)

    # test with default env (prod)
    with pytest.raises(ConfmeException):
        _ = RootConfig.get()

    # test with strict env (prod)
    os.environ['ENV'] = prod_exact_name
    root_config = RootConfig.get()
    assert root_config.childNode.testStr == 'prod-env'

    # test with strict env (test)
    os.environ['ENV'] = 'test'
    with pytest.raises(ConfmeException):
        _ = RootConfig.get()

    os.environ['ENV'] = test_exact_name
    root_config = RootConfig.get()
    assert root_config.childNode.testStr == 'test-env'
