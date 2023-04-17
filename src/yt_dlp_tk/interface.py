from __future__ import annotations
from tkinter import ttk, constants as tkconst
import tkinter as tk
from typing import TYPE_CHECKING, Any, cast, overload, Protocol, Callable
from .logging import get_logger
from .signals import signal, InvalidSignalError

_Column = tuple[str, str, int]

if TYPE_CHECKING:
    from typing import Literal, Type
    _Widget = tk.Widget | None
    _StateSpec = Literal['normal', 'disabled'] | tuple[str, ...]

class _SupportsStateMethods(Protocol):
    def state(self, *args) -> Any:
        ...

class _ResourceManager:
    __slots__ = ('resources',)

    def __init__(self, **kw: Any):
        self.resources: dict[str, Any] = {k: v for k, v in kw.items()}

    def __getitem__(self, key: str, /) -> Any:
        return self.resources[key]

    def __setitem__(self, key: str, value: Any, /) -> None:
        self.resources[key] = value

    def __contains__(self, key: str) -> bool:
        return self.resources.__contains__(key)

class _WidgetMixin:
    @classmethod
    def override_init_docstring(cls, parent: Type[tk.Widget]) -> None:
        import re
        parent_doc = cast(str, parent.__init__.__doc__)
        new_doc = parent_doc + cast(str, cls.__init__.__doc__)
        m = re.search(r'a[ ]*(.*?widget)', r'an extended \1')
        if m is not None:
            pass
        # new_doc = re.sub(r'a[ ]*(.*?widget)', r'an extended \1', new_doc)
        cls.__init__.__doc__ = new_doc

    def override_geomtry_methods(self, cls: Type[tk.Widget]) -> None:
        frame: ttk.Frame = getattr(self, 'frame')

        # HACK: Copy geometry methods of self.frame without overriding other methods
        entry_methods = vars(cls).keys()
        methods = vars(tk.Pack).keys() | vars(tk.Grid).keys() | vars(tk.Place).keys()
        methods = methods.difference(entry_methods)

        for m in methods:
            if m [0] != "_" and m not in ("config", "configure"):
                setattr(self, m, getattr(frame, m))

    def __str__(self) -> str:
        return self.frame.__str__() # pyright: ignore

    # Resource functions

    def set_custom_resources(self, **kw: Any) -> None:
        self.__options = _ResourceManager(**kw)

    def set_custom_resource(self, key: str, value: Any) -> None:
        self.__options[key] = value

    def get_custom_resource(self, key: str) -> Any:
        return self.__options[key]

    def resource_defined(self, key: str) -> bool:
        # Return true if KEY is defined in self._options
        return key in self.__options

class InState:
    """
    Used for temporary state changes of widgets.

    Can be used with a context manager.
    """

    def __init__(self, owner: _SupportsStateMethods, state_spec: _StateSpec):
        self.owner = owner
        self.state_spec = state_spec
        self.old_state: str = owner.state(None)

    def __enter__(self):
        self.owner.state(self.state_spec)

    def __exit__(self, exc_type, exc_value, traceback): # pyright: ignore
        self.owner.state(self.old_state)

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
        self.on_state_changed = signal('state_changed')
        self.on_state_changed.connect(self)

        self.on_y_scrollbar_changed = signal('y_scrollbar_changed')
        self.on_y_scrollbar_changed.connect(self)

        self.on_background_changed = signal('background_changed')
        self.on_background_changed.connect(self)

        self.frame = ttk.Frame(master)
        self.ybar = ttk.Scrollbar(self.frame, orient=tkconst.VERTICAL, command=self.yview)

        kw['yscrollcommand'] = self.ybar.set

        assert state in ('normal', 'disabled')

        super().__init__(self.frame, state=state, **kw)

        # Custom resources
        def _default_bg(color: str | None, *state_flags: str):
            defbg = ttk.Style().lookup('TEntry', 'fieldbackground', state_flags)
            print(state_flags, defbg, color)
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

    # if __debug__:
    #     @property
    #     def y_scrollbar_mapped(self) -> bool:
    #         """True if the y scrollbar is mapped."""
    #         return self.ybar.winfo_ismapped()

class ExEntry(ttk.Entry, _WidgetMixin):
    """Extended entry widget."""

    def __init__(self, master: _Widget=None, *, scrollx: bool=False,
                 text: str | None=None, **kw: Any):
        """
        EXTRA OPTIONS

            scrollx = if true, add a scrollbar
            text    = specify a textual string to display next
                      to the entry

        SIGNALS

            x_scrollbar_changed(state: bool)
                The horizontal scrollbar has changed. STATE
                is true if enabled and false otherwise.

            text_changed(new_text: str)
                The 'text' parameter has changed. Provides
                the new string for the label.
        """
        self.on_x_scrollbar_changed = signal('x_scrollbar_changed')
        self.on_x_scrollbar_changed.connect(self)

        self.on_text_changed = signal('text_changed')
        self.on_text_changed.connect(self)

        self.frame = ttk.Frame(master, padding='0 0 0 16')
        self.label = ttk.Label(self.frame, text=text or "")
        self.xbar = ttk.Scrollbar(self.frame, orient=tkconst.HORIZONTAL, command=self.xview)

        kw['xscrollcommand'] = self.xbar.set

        super().__init__(self.frame, **kw)

        self.entry_name = ttk.Entry.__str__(self)

        # Custom resources
        self.set_custom_resources(scrollx=scrollx, text=text)
        self.on_x_scrollbar_changed.emit(scrollx)
        self.on_text_changed.emit(text or "")

        self.pack()

        self.override_geomtry_methods(ttk.Entry)

    def configure(self, *, scrollx: bool | None=None,
                  text: str | None=None, **kw: Any):
        if scrollx is not None:
            self.set_custom_resource('scrollx', scrollx)
            self.on_x_scrollbar_changed.emit(scrollx)

        if text is not None:
            self.set_custom_resource('text', text)
            self.on_text_changed.emit(text)

        super().configure(kw)

    def cget(self, key: str) -> Any:
        if self.resource_defined(key):
            return self.get_custom_resource(key)

        return super().cget(key)

    def config(self, *, scrollx: bool | None=None,
                  text: str | None=None, **kw: Any):
        return self.configure(scrollx=scrollx, text=text, **kw)

    def on_notify(self, sig: str, obj=None, *args: Any, **kw: Any) -> None: # pyright: ignore
        match sig:
            case 'x_scrollbar_changed':
                scrollx: bool = args[0]
                if scrollx:
                    self.xbar.pack(side=tkconst.BOTTOM, fill=tkconst.X)
                else:
                    self.xbar.pack_forget()

            case 'text_changed':
                text: str = args[0]
                label = self.label
                if text:
                    kw = {}
                    if not label.winfo_ismapped():
                        if self.frame.winfo_ismapped():
                            kw['before'] = self.entry_name
                        label.pack(**kw)
                    label.configure(text=text)
                else:
                    if label.winfo_ismapped():
                        label.pack_forget()

            case _:
                raise InvalidSignalError(sig)

class ExTree(ttk.Treeview, _WidgetMixin):
    """Extended treeview widget."""

    def __init__(self, master: _Widget=None,
                 scrolly: bool=False, scrollx: bool=False,
                 columns: list[_Column] | None=None,
                 **kw: Any):
        """
        EXTRA OPTIONS

            scrolly = if true, add a vertical scrollbar
            scrollx = if true, add a horizontal scrollbar
            columns = write-only, only present in init. 
                      Specify the IDs, headings, and widths
                      of columns

        SIGNALS

            x_scrollbar_changed()
                * The horizontal scrollbar has changed, either
                  true if it is enabled or false otherwise

            y_scrollbar_changed(state: bool)
                * The vertical scrollbar has changed, either
                  true if it is enabled or false otherwise
        """
        logger = self.logger = get_logger('gui.widgets.ExTree', stream=True)

        # Signals
        self.on_x_scrollbar_changed = signal('x_scrollbar_changed')
        self.on_x_scrollbar_changed.connect(self)

        self.on_y_scrollbar_changed = signal('y_scrollbar_changed')
        self.on_y_scrollbar_changed.connect(self)

        self.frame = ttk.Frame(master)
        self.xbar = ttk.Scrollbar(self.frame, orient=tkconst.HORIZONTAL, command=self.xview)
        self.ybar = ttk.Scrollbar(self.frame, orient=tkconst.VERTICAL, command=self.yview)

        kw['xscrollcommand'] = self.xbar.set
        kw['yscrollcommand'] = self.ybar.set

        # Special option: columns
        column_ids: list[str] = []

        if isinstance(columns, list):            
            for cid, hd, _ in columns:
                column_ids.append(cid)

            if column_ids:
                kw['columns'] = column_ids

        super().__init__(self.frame, **kw)

        if column_ids:
            for cid, hd, w in cast(list[_Column], columns):
                logger.debug("Change column %s by setting label to %s and width to %d", cid, hd, w)
                self.column(cid, width=w)
                self.heading(cid, text=hd)

        # Custom resources
        self.set_custom_resources(scrolly=scrolly, scrollx=scrollx)

        self.on_x_scrollbar_changed.emit(scrollx)
        self.on_y_scrollbar_changed.emit(scrolly)

        # Render the tree widget
        self.pack()

        self.override_geomtry_methods(ttk.Treeview)

    def cget(self, key: str) -> Any:
        if self.resource_defined(key):
            return self.get_custom_resource(key)

        return super().cget(key)

    def configure(self, *, scrolly: bool | None=None,
                  scrollx: bool | None=None, **kw: Any):
        if scrollx is not None:
            self.set_custom_resource('scrollx', scrollx)
            self.on_x_scrollbar_changed.emit(scrollx)

        if scrolly is not None:
            self.set_custom_resource('scrolly', scrolly)
            self.on_y_scrollbar_changed.emit(scrolly)

        super().configure(kw)

    def on_notify(self, sig: str, obj: Any, *args: Any, **kw: Any) -> None: # pyright: ignore
        match sig:
            case 'x_scrollbar_changed':
                state: bool = args[0]
                if state:
                    self.xbar.pack(side=tkconst.BOTTOM, fill=tkconst.X)
                else:
                    self.xbar.pack_forget()

            case 'y_scrollbar_changed':
                state: bool = args[0]
                if state:
                    self.ybar.pack(side=tkconst.RIGHT, fill=tkconst.Y)
                else:
                    self.ybar.pack_forget()

            case _: # pragma: no cover
                raise InvalidSignalError(sig)

    if __debug__:
        @property
        def x_scrollbar_mapped(self) -> bool:
            """True if the x scrollbar is mapped."""
            return self.xbar.winfo_ismapped()

        @property
        def y_scrollbar_mapped(self) -> bool:
            """True if the y scrollbar is mapped."""
            return self.ybar.winfo_ismapped()

ExEntry.override_init_docstring(ttk.Entry)
ExText.override_init_docstring(tk.Text)
ExTree.override_init_docstring(ttk.Treeview)
