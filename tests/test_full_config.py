import logging
import os
import uuid
from enum import Enum
from os import path
from typing import Optional

import pytest

from confme import BaseConfig
from confme.annotation import Secret, ClosedRange


class AnyEnum(Enum):
    V1 = 'value1'
    V2 = 'value2'


class ChildNode(BaseConfig):
    # das ist ein kommentar für den string
    testStr: str  # das ist ein anderer kommentar für den string
    testInt: int
    # das ist ein kommentar for floats
    testFloat: float
    testOptional: Optional[float]
    password: str = Secret('highSecure')
    anyEnum: AnyEnum


class RootConfig(BaseConfig):
    rootValue: int
    rangeValue: int = ClosedRange(4, 6)
    childNode: ChildNode


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
