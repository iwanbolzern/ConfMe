import os
import uuid
from os import path

import pytest

from confme import BaseConfig
from confme.annotation import Secret, Range


class ChildNode(BaseConfig):
    testStr: str
    testInt: int
    testFloat: float
    password: str = Secret('highSecure')


class RootConfig(BaseConfig):
    rootValue: int
    rangeValue: int = Range(4, None, 6)
    childNode: ChildNode


@pytest.fixture
def config_yaml(tmp_path: str):
    config_content = 'rootValue: 1\n' \
                     'rangeValue: 5\n' \
                     'childNode:\n' \
                     '  testStr: "Das ist ein test"\n' \
                     '  testInt: 42\n' \
                     '  testFloat: 42.42\n'

    config_path = path.join(tmp_path, f'{uuid.uuid4()}.yaml')
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)

    return config_path


def test_load_config(config_yaml: str):
    os.environ['highSecure'] = 'superSecureSecret'

    root_config = RootConfig.load(config_yaml)

    assert root_config.rootValue == 1
    assert root_config.rangeValue == 5
    assert root_config.childNode.testStr == 'Das ist ein test'
    assert root_config.childNode.testInt == 42
    assert root_config.childNode.testFloat == 42.42
    assert root_config.childNode.password == os.environ['highSecure']
