# module of all supported annotations
import os
from typing import Any

import pydantic
from pydantic import Field


def EnvField(default: Any, *, env_var: str, **kwargs: Any):
    return Field(default_factory=lambda: os.environ.get(env_var, default), **kwargs)


def Secret(env_var: str):
    return EnvField(..., env_var=env_var)


def OpenRange(gt: float | None = None, lt: float | None = None):
    return Field(..., gt=gt, lt=lt)


def ClosedRange(ge: float | None = None, le: float | None = None):
    return Field(..., ge=ge, le=le)


def MixedRange(
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
):
    return Field(..., gt=gt, ge=ge, lt=lt, le=le)


__all__ = list(pydantic.__all__) + [Secret, OpenRange, ClosedRange, MixedRange]  # pyright: ignore[reportUnsupportedDunderAll]
