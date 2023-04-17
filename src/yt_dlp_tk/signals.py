from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Any

class InvalidSignalError(RuntimeError):
    """Invalid signal."""

class observer(Protocol):
    """An observer that takes one or more signals."""

    def on_notify(self, sig: str, obj: Any, *args: Any, **kw: Any):
        """Called when OBJ has notified of SIGNAL."""
        ...

class signal:
    """Implements the observer pattern."""

    __slots__ = ('name', 'observers', 'observer_count', 'obj')

    def __init__(self, name: str, obj=None):
        self.name = name
        self.observers: list[observer] = []
        self.observer_count = 0
        self.obj: object | None = obj

    def connect(self, obj: observer, /):
        """Connect to the observer OBJ."""
        self.observers.append(obj)
        self.observer_count += 1

    def disconnect(self, obj: observer, /):
        """Disconnect from the observer OBJ."""
        self.observers.remove(obj)
        self.observer_count -= 1

    def emit(self, *args: Any, **kw: Any):
        """
        Emit the signal.

        Notify all connected observers of the event.
        """
        for obv in self.observers:
            obv.on_notify(self.name, self.obj, *args, **kw)

    def __str__(self) -> str:
        return self.name
