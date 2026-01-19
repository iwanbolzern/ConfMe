from enum import Enum
from typing import Optional

from confme import BaseConfig
from confme.annotation import ClosedRange, Secret


class AnyEnum(Enum):
    V1 = "value1"
    V2 = "value2"


class ChildNode(BaseConfig):
    # this is a comment for string
    testStr: str  # this is another comment for a string
    testInt: int
    # this is a comment for float
    testFloat: float
    testOptional: Optional[float] = None
    password: str = Secret("highSecure")
    anyEnum: AnyEnum


class RootConfig(BaseConfig):
    rootValue: int
    rangeValue: int = ClosedRange(4, 6)
    childNode: ChildNode


class FlatConfig(BaseConfig):
    oneValue: int
    twoValue: str
