from typing import Dict

import pytest

from confme.core.default_gen import Generator
from tests.unit.config_model import RootConfig


@pytest.fixture
def expected_dict():
    return {'rootValue': 42,
            'rangeValue': 42,
            'childNode': {
                'testStr': 'bla',
                'testInt': 42,
                'testFloat': 42.42,
                'testOptional': 42.42,
                'password': 'bla',
                'anyEnum': 'value1'
            }}


def test_load_config_from_dict(expected_dict: Dict):
    gen = Generator()
    res = gen.generate(RootConfig)

    assert res == expected_dict
