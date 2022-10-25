import logging
import os
import uuid
from os import path
from typing import Dict

import pytest

from confme import ConfmeException
from tests.unit.config_model import RootConfig, AnyEnum, FlatConfig


@pytest.fixture
def config_yaml(tmp_path: str):
    config_content = 'rootValue: 1\n' \
                     'rangeValue: 5\n' \
                     'childNode:\n' \
                     '  testStr: "This is a test"\n' \
                     '  testInt: 42\n' \
                     '  testFloat: 42.42\n' \
                     '  anyEnum: value2'

    config_path = path.join(tmp_path, f'{uuid.uuid4()}.yaml')
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)

    return config_path


@pytest.fixture
def config_dict(tmp_path: str):
    return {'rootValue': 1,
            'rangeValue': 5,
            'childNode': {
                'testStr': 'This is a test',
                'testInt': 42,
                'testFloat': 42.42,
                'anyEnum': 'value2'
            }}


@pytest.fixture
def flat_config_yaml(tmp_path: str):
    config_content = 'oneValue: 1\n' \
                     'twoValue: "This is a test"'

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
    assert root_config.childNode.testStr == 'This is a test'
    assert root_config.childNode.testInt == 42
    assert root_config.childNode.testFloat == 42.42
    assert root_config.childNode.testOptional is None
    assert root_config.childNode.password == os.environ['highSecure']
    assert root_config.childNode.anyEnum == AnyEnum.V2


def test_load_flat_config(flat_config_yaml: str):
    flat_config = FlatConfig.load(flat_config_yaml)
    logging.info(f'Config loaded: {flat_config.dict()}')

    assert flat_config.oneValue == 1
    assert flat_config.twoValue == 'This is a test'


def test_load_conifg_from_dict(config_dict: Dict):
    os.environ['highSecure'] = 'superSecureSecret'

    root_config = RootConfig.load_from_dict(config_dict)
    logging.info(f'Config loaded: {root_config.dict()}')

    assert root_config.rootValue == 1
    assert root_config.rangeValue == 5
    assert root_config.childNode.testStr == 'This is a test'
    assert root_config.childNode.testInt == 42
    assert root_config.childNode.testFloat == 42.42
    assert root_config.childNode.testOptional is None
    assert root_config.childNode.password == os.environ['highSecure']
    assert root_config.childNode.anyEnum == AnyEnum.V2


def test_update_by_str(config_yaml: str):
    os.environ['highSecure'] = 'superSecureSecret'

    root_config = RootConfig.load(config_yaml)
    logging.info(f'Config loaded: {root_config.dict()}')

    root_config.update_by_str('rootValue', 10)
    root_config.update_by_str('childNode.testStr', 'This str was changed')

    assert root_config.rootValue == 10
    assert root_config.childNode.testStr == 'This str was changed'

    with pytest.raises(ConfmeException):
        root_config.update_by_str('rootValue2', 10)

    with pytest.raises(ConfmeException):
        root_config.update_by_str('childNode2.testStr', 10)


def test_get_flat_rep(config_yaml: str):
    os.environ['highSecure'] = 'superSecureSecret'

    root_config = RootConfig.load(config_yaml)
    logging.info(f'Config loaded: {root_config.dict()}')

    flat_repr = root_config.get_flat_repr()
    assert flat_repr[0] == ('rootValue', 1)
    assert flat_repr[1] == ('rangeValue', 5)
    assert flat_repr[2] == ('childNode.testStr', 'This is a test')
    assert flat_repr[3] == ('childNode.testInt', 42)
    assert flat_repr[4] == ('childNode.testFloat', 42.42)
    assert flat_repr[5] == ('childNode.testOptional', None)
    assert flat_repr[6] == ('childNode.password', os.environ['highSecure'])
    assert flat_repr[7] == ('childNode.anyEnum', AnyEnum.V2)


def test_generate_example():
    expected_output = 'rootValue: 42\n' \
                       'rangeValue: 42\n' \
                       'childNode:\n' \
                       '  testStr: "bla"\n' \
                       '  testInt: 42\n' \
                       '  testFloat: 42.42\n' \
                       '  testOptional: 42.42\n' \
                       '  password: "bla"\n' \
                       '  anyEnum: value1'
    output = None
    def _print(out: str):
        nonlocal output
        output = out

    RootConfig.generate_example(_print)

    assert output == expected_output



