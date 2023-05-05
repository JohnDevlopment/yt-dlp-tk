from __future__ import annotations
from tkinter import ttk, constants as tkconst
from .utils import _WidgetMixin
from ..signals import signal, InvalidSignalError
from typing import TYPE_CHECKING
import tkinter as tk, sys

if TYPE_CHECKING:
    from typing import Any
    from .utils import _Widget

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
        self.on_x_scrollbar_changed = signal('x_scrollbar_changed', self)
        self.on_x_scrollbar_changed.connect(self)

        self.on_text_changed = signal('text_changed', self)
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

ExEntry.override_init_docstring(ttk.Entry)

def _test_nontemp_variables():
    from .utils import StringVar

    for varname in ['NAME', 'RADIO']:
        var = StringVar(name=varname)
        print(f"{varname}:", var.get())

def _test_temp_variables():
    from .utils import StringVar

    for varname in ['TEMPNAME', 'TEMPRADIO']:
        var = StringVar(name=varname, temp=True)
        print(f"{varname}:", var.get())

def make_interface():
    from .utils import StringVar

    root = tk.Tk()
    root.title("Test ExEntry")

    frame = ttk.Frame()
    frame.pack(fill=tkconst.BOTH, expand=True)

    # Non-temp variables
    subframe = ttk.Labelframe(frame, text="Non-Temp Vars")
    subframe.pack()

    ExEntry(subframe, text="Name", textvariable=StringVar(name='NAME'))\
        .pack()

    var = StringVar(name='RADIO', value='one')
    ttk.Radiobutton(subframe, variable=var, value='one', text="One").pack()
    ttk.Radiobutton(subframe, variable=var, value='two', text="Two").pack()
    ttk.Radiobutton(subframe, variable=var, value='three', text="Three").pack()

    ttk.Button(subframe, text='Test', command=_test_nontemp_variables).pack()

    # Temp variables
    subframe = ttk.Labelframe(frame, text="Temp Vars")
    subframe.pack()

    ExEntry(subframe, text="Temp Name", textvariable=StringVar(name='TEMPNAME', temp=True))\
        .pack()

    var = StringVar(name='TEMPRADIO', value='one', temp=True)
    ttk.Radiobutton(subframe, variable=var, value='one', text="One").pack()
    ttk.Radiobutton(subframe, variable=var, value='two', text="Two").pack()
    ttk.Radiobutton(subframe, variable=var, value='three', text="Three").pack()

    ttk.Button(subframe, text='Test', command=_test_temp_variables).pack()

    return root

def test () -> int:
    root = make_interface()
    root.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(test())
