# module of all supported annotations

import pydantic
from pydantic import Field


def Secret(env_var: str):
    return Field(..., env=env_var)


def OpenRange(gt: float = None, lt: float = None) -> Field:
    return Field(..., gt=gt, lt=lt)


def ClosedRange(ge: float = None, le: float = None):
    return Field(..., ge=ge, le=le)


def MixedRange(gt: float = None, ge: float = None, lt: float = None, le: float = None):
    return Field(..., gt=gt, ge=ge, lt=lt, le=le)


__all__ = pydantic.__all__ + [Secret, OpenRange, ClosedRange, MixedRange]
