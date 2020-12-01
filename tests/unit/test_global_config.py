import os
import uuid
from pathlib import Path

import pytest
from confme import GlobalConfig
from tests.unit.config_model import GlobalRootConfig


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
                     '  testStr: "test-env"\n' \
                     '  testInt: 42\n' \
                     '  testFloat: 42.42\n' \
                     '  anyEnum: value2'

    config_path = Path(tmp_path) / f'{uuid.uuid4()}_prod.yaml'
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)

    return str(config_path)


def test_load_config(prod_config_yaml: str, test_config_yaml: str):
    os.environ['highSecure'] = 'superSecureSecret'
    os.environ['ENV'] = 'test'

    GlobalRootConfig.register_folder(Path(prod_config_yaml).parent)
    root_config = GlobalRootConfig.get()
    print(root_config)

    # root_config = RootConfig.load(config_yaml)
    # logging.info(f'Config loaded: {root_config.dict()}')
    #
    # assert root_config.rootValue == 1
    # assert root_config.rangeValue == 5
    # assert root_config.childNode.testStr == 'This is a test'
    # assert root_config.childNode.testInt == 42
    # assert root_config.childNode.testFloat == 42.42
    # assert root_config.childNode.testOptional is None
    # assert root_config.childNode.password == os.environ['highSecure']
    # assert root_config.childNode.anyEnum == AnyEnum.V2
