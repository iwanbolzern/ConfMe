# module of all supported annotations

import pydantic
from pydantic import Field


def Secret(env_var: str):
    return Field(..., env=env_var)


def Range(gt: float = None, ge: float = None, lt: float = None, le: float = None):
    return Field(..., gt=gt, ge=ge, lt=lt, le=le)


__all__ = pydantic.__all__ + [Secret, Range]
