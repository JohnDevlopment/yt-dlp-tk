"""Display a toplevel window with a console."""

from __future__ import annotations
from . import ExText
from .utils import InState
from ..logging import get_logger, add_handler
from ..signals import signal
from tkinter import ttk, Misc, constants as tkconst, Toplevel
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from typing import Any, Type
    from typing_extensions import Self

class ConsoleWindow(Toplevel):
    """Console window."""

    _instance: ConsoleWindow | None = None

    LINE_LIMIT = 200

    @classmethod
    def show(cls: Type[Self]) -> Self:
        """
        Show the console window.

        Creates the window on first invocation, then
        returns it on successive calls.
        """
        if cls._instance is None:
            cls._instance = cls()
            return cls._instance

        inst = cls._instance
        inst.deiconify()
        inst.clear()
        inst.update()
        inst.on_show.emit()
        return inst

    def __init__(self, master: Misc | None=None,
                 cnf: dict[str, Any]={}, **kw: Any):
        super().__init__(master, cnf, **kw)
        self._body()
        self._mapped = True
        self.on_show = signal('show', self)
        self.on_close = signal('close', self)

    def _body(self):
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tkconst.BOTH, expand=True)

        self.text = ExText(self.frame, state='disabled', scrolly=True)
        self.text.pack(fill=tkconst.BOTH)

        ttk.Button(self.frame, text="Close", command=self.close).pack()

    def write(self, text: str, /):
        with InState(self.text, 'normal'):
            self.text.insert(tkconst.END, text)
            self.text.see(tkconst.END)

    def clear(self):
        with InState(self.text, 'normal'):
            self.text.delete(1.0, 'end')

    def flush(self):
        self.update()

    def close(self):
        self.wm_withdraw()
        self.on_close.emit()

def test ():
    from tkinter import ttk
    import tkinter as tk

    root = tk.Tk()
    root.geometry('320x240')
    root.title("Console Test")

    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    def _btn1_cmd():
        logger = get_logger('tests.gui.console', stream=False)
        console = ConsoleWindow.show()

        def log():
            logger.debug("Test line.")
            logger.info("Test line.")
            logger.warning("Test line.")
            logger.error("Test line.")
            logger.critical("Test line.")

        console.after(1000, log)

    button = ttk.Button(frame, text='Show Console')
    button.config(command=_btn1_cmd)
    button.pack()

    def on_show(obj: object, *args, **kw):
        button: ttk.Button = kw['button']
        button.state(('disabled',))
        print("Disabled button")

    def on_close(obj: object, *args, **kw):
        console = cast(ConsoleWindow, obj)
        console.clear()
        print("Console cleared")
        button: ttk.Button = kw['button']
        button.state(('!disabled',))

    # Initialize the console, connect to its signals,
    # and add it to a logger object
    console = ConsoleWindow.show()
    console.on_show.connect(on_show, button=button)
    console.on_close.connect(on_close, button=button)
    add_handler(
        get_logger('tests.gui.console', stream=False),
        'stream', stream=console)
    console.close()
    del console

    root.mainloop()

if __name__ == "__main__":
    test()
