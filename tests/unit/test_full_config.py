import logging
import os
import uuid
from os import path

import pytest

from tests.unit.config_model import RootConfig, AnyEnum, FlatConfig


@pytest.fixture
def config_yaml(tmp_path: str):
    config_content = 'rootValue: 1\n' \
                     'rangeValue: 5\n' \
                     'childNode:\n' \
                     '  testStr: "Das ist ein test"\n' \
                     '  testInt: 42\n' \
                     '  testFloat: 42.42\n' \
                     '  anyEnum: value2'

    config_path = path.join(tmp_path, f'{uuid.uuid4()}.yaml')
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)

    return config_path


@pytest.fixture
def flat_config_yaml(tmp_path: str):
    config_content = 'oneValue: 1\n' \
                     'twoValue: "Das ist ein test"'

    config_path = path.join(tmp_path, f'{uuid.uuid4()}.yaml')
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)

    return config_path


def test_load_config(config_yaml: str):
    os.environ['highSecure'] = 'superSecureSecret'

    root_config = RootConfig.load(config_yaml)
    logging.info(f'Config loaded: {root_config.dict()}')

    assert root_config.rootValue == 1
    assert root_config.rangeValue == 5
    assert root_config.childNode.testStr == 'Das ist ein test'
    assert root_config.childNode.testInt == 42
    assert root_config.childNode.testFloat == 42.42
    assert root_config.childNode.testOptional is None
    assert root_config.childNode.password == os.environ['highSecure']
    assert root_config.childNode.anyEnum == AnyEnum.V2


def test_load_flat_config(flat_config_yaml: str):

    flat_config = FlatConfig.load(flat_config_yaml)
    logging.info(f'Config loaded: {flat_config.dict()}')

    assert flat_config.oneValue == 1
    assert flat_config.twoValue == 'Das ist ein test'
