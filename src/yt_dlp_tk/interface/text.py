from __future__ import annotations
from tkinter import ttk, constants as tkconst
from .utils import _WidgetMixin
from ..signals import signal, InvalidSignalError
from typing import TYPE_CHECKING, Callable, overload
import tkinter as tk

if TYPE_CHECKING:
    from typing import Any
    from .utils import _Widget, _StateSpec

class ExText(tk.Text, _WidgetMixin):
    """Extended text widget."""

    def _tk_color_name_to_number(self, color: str) -> str:
        import re
        if re.match(r'#[0-9a-f]{6}', color):
            return color
        r, g, b = self.winfo_rgb(color)
        icolor = ((r & 0xff00) << 8) | (g & 0xff00) | (b >> 8)
        return f"#{icolor:06x}"

    def __init__(self, master: _Widget=None, *, scrolly: bool=False,
                 state: _StateSpec='normal',
                 normalbackground: str | None=None,
                 disabledbackground: str | None=None,
                 **kw):
        """
        EXTRA OPTIONS

            scrolly = if true, add a vertical scrollbar
            state = the state the widget should be in ('normal' or 'disabled')
            disabledbackground = the background color when the widget is disabled
            normalbackground = the background color when the widget is enabled
            **kw = options passed to tkinter.Text

        SIGNALS

            state_changed(state: str)
                The state has changed. STATE is the updated widget state,
                either 'normal' or 'disabled'.

            y_scrollbar_changed(state: bool)
                The state of the vertical scrollbar has changed. STATE is
                true if the scrollbar is enabled and false otherwise.

            background_changed(state: str, color: str)
                A state-dependent background color option has been changed.
                STATE is either 'normal' or 'disabled'. COLOR is the
                updated color of the background.
        """
        # Signals
        self.on_state_changed = signal('state_changed', self)
        self.on_state_changed.connect(self)

        self.on_y_scrollbar_changed = signal('y_scrollbar_changed', self)
        self.on_y_scrollbar_changed.connect(self)

        self.on_background_changed = signal('background_changed', self)
        self.on_background_changed.connect(self)

        self.frame = ttk.Frame(master)
        self.ybar = ttk.Scrollbar(self.frame, orient=tkconst.VERTICAL, command=self.yview)

        kw['yscrollcommand'] = self.ybar.set

        assert state in ('normal', 'disabled')

        super().__init__(self.frame, state=state, **kw)

        # Custom resources
        def _default_bg(color: str | None, *state_flags: str):
            defbg = ttk.Style().lookup('TEntry', 'fieldbackground', state_flags)
            return color or defbg

        self.set_custom_resources(
            disabledbackground='#262626',
            normalbackground='white',
            scrolly=False
        )

        self.configure(
            disabledbackground=_default_bg(disabledbackground, 'disabled'),
            normalbackground=_default_bg(normalbackground, '!disabled'),
            scrolly=scrolly
        )

        self.on_state_changed.emit(state)
        self.on_y_scrollbar_changed.emit(scrolly)

        # Render the text widget
        self.pack(side=tkconst.LEFT, ipadx=16)

        self.override_geomtry_methods(tk.Text)

    def cget(self, key: str) -> Any:
        if self.resource_defined(key):
            return self.get_custom_resource(key)

        return super().cget(key)

    def configure(self, *,
                  disabledbackground: str | None=None,
                  normalbackground: str | None=None,
                  scrolly: bool | None=None, **kw: Any):
        if disabledbackground is not None:
            self.set_custom_resource(
                'disabledbackground',
                self._tk_color_name_to_number(disabledbackground)
            )
            self.on_background_changed.emit('disabled', disabledbackground)

        if normalbackground is not None:
            self.set_custom_resource(
                'normalbackground',
                self._tk_color_name_to_number(normalbackground)
            )
            self.on_background_changed.emit('normal', normalbackground)

        if scrolly is not None:
            self.set_custom_resource('scrolly', scrolly)
            self.on_y_scrollbar_changed.emit(scrolly)

        super().configure(kw)

        if 'state' in kw:
            self.on_state_changed.emit(kw['state'])

    def on_notify(self, sig: str, obj=None, *args: Any, **kw: Any): # pyright: ignore
        """Signal handler."""
        match sig:
            case 'state_changed':
                state: str = args[0]
                color: str = self.cget(state + 'background')
                self.config(background=color)

            case 'y_scrollbar_changed':
                scrolly: bool = args[0]
                if scrolly:
                    self.ybar.pack(side=tkconst.RIGHT, fill=tkconst.Y)
                else:
                    self.ybar.pack_forget()

            case 'background_changed':
                bgstate, color = args
                if self.state() == bgstate:
                    super().configure(background=color)

            case _:
                raise InvalidSignalError(sig)

    config = configure

    # State functions

    @overload
    def state(self, state_spec: None=None) -> str:
        ...

    @overload
    def state(self, state_spec: _StateSpec) -> None:
        ...

    def state(self, state_spec=None):
        """
        Query or modify the widget state.

        If STATE_SPEC is provided, the widget state
        is changed to match STATE_SPEC, otherwise the
        current state is returned.
        """
        if state_spec is None:
            return self.cget('state')
        self.configure(state=state_spec)

    def instate(self, state_spec: _StateSpec,
                callback: Callable[..., None] | None=None,
                *args, **kw) -> bool | None:
        """
        Test the widget's state.

        If CALLBACK is not provided, returns true
        if the widget state matches STATE_SPEC;
        otherwise CALLBACK is called with *ARGS
        and **KW if the widget state matches.
        """
        test = self.state() == state_spec
        if callback is None:
            return test

        if test:
            callback(*args, **kw)

ExText.override_init_docstring(tk.Text)
