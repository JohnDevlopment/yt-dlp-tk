from __future__ import annotations
from typing import Protocol, overload, cast, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TypeGuard

class InvalidSignalError(RuntimeError):
    """Invalid signal."""

class observer(Protocol):
    """An observer that takes one or more signals."""

    def on_notify(self, sig: str, obj: Any, *args: Any, **kw: Any):
        """Called when OBJ has notified of signal SIG."""
        ...

class _signal_function(Protocol):
    def __call__(self, obj: object, *args: Any, **kw: Any) -> None:
        ...

_SignalBinds = tuple[_signal_function, tuple[Any, ...], dict[str, Any]]

class signal:
    """Implements the observer pattern."""

    __slots__ = ('name', 'observers', 'observer_count', 'obj')

    def __init__(self, name: str, obj: object=None):
        """
        Initialize the signal with the given NAME.

        OBJ is the object to which this signal belongs.
        If OBJ is omitted or None, the 'self' argument
        of the caller is used instead; if 'self' is
        undefined, the module is used.
        """
        self.name = name
        self.observers: list[observer | _SignalBinds] = []
        self.observer_count = 0

        self.obj = obj

        if obj is None:
            import inspect, sys

            # Get current frame
            frame = inspect.currentframe()
            if frame is None: return

            # Go up one level, to the function calling this one
            frame = frame.f_back
            if frame is None: return

            # Get the 'self' argument if present
            _locals = frame.f_locals
            obj = _locals.get('self')
            if obj is None:
                # Not present, use the module instead
                obj = sys.modules[frame.f_globals['__name__']]

            self.obj = obj

    def _form_signal_bind(self, fn: _signal_function,
                          *args: Any, **kw: Any):
        return fn, args, kw

    @overload
    def connect(self, obj_or_func: observer,
                *binds: Any, **kw: Any) -> None:
        ...

    @overload
    def connect(self, obj_or_func: _signal_function,
                *binds: Any, **kw: Any) -> None:
        ...

    def connect(self, obj_or_func, *binds, **kw):
        """Connect to the observer OBJ."""
        if callable(obj_or_func):
            bind = self._form_signal_bind(obj_or_func, *binds, **kw)
            self.observers.append(bind)
        else:
            self.observers.append(obj_or_func)

        self.observer_count += 1

    @overload
    def disconnect(self, obj_or_func: observer,
                   *binds: Any, **kw: Any) -> None:
        ...

    @overload
    def disconnect(self, obj_or_func: _signal_function,
                   *binds: Any, **kw: Any) -> None:
        ...

    def disconnect(self, obj_or_func, *binds, **kw):
        """Disconnect from the observer OBJ."""
        if callable(obj_or_func):
            bind = self._form_signal_bind(obj_or_func, *binds, **kw)
            self.observers.remove(bind)
        else:
            self.observers.remove(obj_or_func)

        self.observer_count -= 1

    @staticmethod
    def _is_signal_bind(arg: observer | _SignalBinds) -> TypeGuard[_SignalBinds]:
        return isinstance(arg, tuple)

    def emit(self, *args: Any, **kw: Any):
        """
        Emit the signal.

        Notify all connected observers of the event.
        """
        for obv in self.observers:
            if self._is_signal_bind(obv):
                fn, sargs, skw = obv
                args = args + sargs
                kw.update(skw)
                fn(self.obj, *args, **kw)
            else:
                cast(observer, obv).on_notify(self.name,
                                              self.obj, *args, **kw)

    def __str__(self) -> str:
        return self.name
