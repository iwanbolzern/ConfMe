from enum import Enum
from typing import Optional

from confme import BaseConfig, GlobalConfig
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


class GlobalRootConfig(GlobalConfig):
    rootValue: int
    rangeValue: int = ClosedRange(4, 6)
    childNode: ChildNode


class FlatConfig(BaseConfig):
    oneValue: int
    twoValue: str
