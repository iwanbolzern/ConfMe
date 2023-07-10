# module of all supported annotations
import os
from typing import Any

import pydantic
from pydantic import Field


def EnvField(default: Any, *, env_var: str, **kwargs):
    return Field(default, default_factory=lambda: os.environ.get(env_var, default=None), **kwargs)


def Secret(env_var: str):
    return EnvField(..., env_var=env_var)


def OpenRange(gt: float = None, lt: float = None) -> Field:
    return Field(..., gt=gt, lt=lt)


def ClosedRange(ge: float = None, le: float = None):
    return Field(..., ge=ge, le=le)


def MixedRange(gt: float = None, ge: float = None, lt: float = None, le: float = None):
    return Field(..., gt=gt, ge=ge, lt=lt, le=le)


__all__ = pydantic.__all__ + [Secret, OpenRange, ClosedRange, MixedRange]
