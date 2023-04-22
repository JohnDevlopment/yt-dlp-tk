"""Display a toplevel window with a console."""

from __future__ import annotations
from ..interface import ExText, InState
from ..logging import get_logger, add_handler
from tkinter import ttk, Misc, constants as tkconst, Toplevel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

class ConsoleWindow(Toplevel):
    """Console window."""

    def __init__(self, master: Misc | None=None,
                 cnf: dict[str, Any]={}, **kw: Any):
        super().__init__(master, cnf, **kw)
        self._body()

    def _body(self):
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tkconst.BOTH, expand=True)

        self.text = ExText(self.frame, state='disabled')
        self.text.pack(fill=tkconst.BOTH)

    def write(self, text: str, /):
        with InState(self.text, 'normal'):
            self.text.insert(tkconst.END, text)

    def flush(self): ...

def test ():
    from tkinter import ttk
    import tkinter as tk

    root = tk.Tk()
    root.geometry('320x240')
    root.title("Console Test")

    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    def _btn1_cmd(btn: ttk.Button):
        btn.after_idle(btn.destroy)

        logger = get_logger('tests.gui.console', stream=False)
        console = ConsoleWindow()
        add_handler(logger, 'stream', stream=console)

        def log():
            logger.debug("Test line.")
            logger.info("Test line.")
            logger.warning("Test line.")
            logger.error("Test line.")
            logger.critical("Test line.")

        console.after(1000, log)

    btn = ttk.Button(frame, text='Show Console')
    btn.config(command=lambda: _btn1_cmd(btn))
    btn.pack()

    root.mainloop()

if __name__ == "__main__":
    test()
