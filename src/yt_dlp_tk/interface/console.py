"""Display a toplevel window with a console."""

from __future__ import annotations
from . import ExText
from .utils import InState
from ..logging import get_logger, add_handler
from ..signals import signal
from tkinter import ttk, Misc, constants as tkconst, Toplevel
from typing import TYPE_CHECKING

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

        cls._instance.deiconify()
        return cls._instance

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

        self.text = ExText(self.frame, state='disabled')
        self.text.pack(fill=tkconst.BOTH)

        ttk.Button(self.frame, text="Close", command=self.close).pack()

    def write(self, text: str, /):
        with InState(self.text, 'normal'):
            self.text.insert(tkconst.END, text)

    def flush(self):
        pass

    def close(self):
        self.wm_withdraw()

def test ():
    from tkinter import ttk
    import tkinter as tk

    root = tk.Tk()
    root.geometry('320x240')
    root.title("Console Test")

    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    def _btn1_cmd(btn: ttk.Button):
        logger = get_logger('tests.gui.console', stream=False)
        console = ConsoleWindow.show()
        add_handler(logger, 'stream', stream=console)

        def log():
            logger.debug("Test line.")
            logger.info("Test line.")
            logger.warning("Test line.")
            logger.error("Test line.")
            logger.critical("Test line.")

        console.after(1000, log)

    button = ttk.Button(frame, text='Show Console')
    button.config(command=lambda: _btn1_cmd(button))
    button.pack()

    root.mainloop()

if __name__ == "__main__":
    test()
