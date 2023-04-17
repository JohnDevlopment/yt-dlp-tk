# Utility functions and classes.

from __future__ import annotations
from typing import TYPE_CHECKING, Generic, TypeVar, cast
from typing_extensions import Self
from enum import IntEnum, unique, auto
import os

if TYPE_CHECKING:
    from typing import Any, Type, TypeGuard

# Result handling
class ErrorEnum(IntEnum):
    """Error enum."""

T = TypeVar('T')
E = TypeVar('E', ErrorEnum, None, covariant=True)

class Result(Generic[T, E]):
    """A result with either an Ok value or an Err value."""

    def __init__(self, ok_value: T, err_value: E=None):
        self.__okval = ok_value
        self.__errval = err_value

    @property
    def ok(self) -> T:
        """The Ok value."""
        return self.__okval

    @property
    def err(self) -> E:
        """The Err value."""
        return self.__errval

###

class EnvError(RuntimeError):
    """Failed to obtain environment variable."""

class ConstantError(RuntimeError):
    """Value cannot be changed."""

class InvalidSignal(RuntimeError):
    """The observer does not support this particular signal."""

class attr_dict(dict):
    """A dictionary that supports attribute notation."""

    def __getattr__(self, key: str) -> Any:
        return self[key]

    def __setattr__(self, key: str, value) -> None:
        self[key] = value

class readonly_dict(dict):
    """A dictionary whose values cannot be changed."""

    def __setitem__(self, key, value):
        raise ConstantError(f"cannot assign elements to {type(self).__name__}")

def get_env(envname: str) -> str | None:
    """Get an environment variable, return None if it doesn't exist."""
    temp = os.getenv(envname)
    return temp
