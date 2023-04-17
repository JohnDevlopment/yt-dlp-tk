from __future__ import annotations
from typing import TYPE_CHECKING, cast
from tkinter import Tk, ttk, BooleanVar, StringVar
from ..interface import ExText, ExEntry, ExTree

if TYPE_CHECKING:
    from typing import Any

def main() -> None:
    root = Tk()

    # ExEntry

    def _callback_checkbutton(entry: ExEntry, field: str, *args):
        match field:
            case 'label':
                text: str = entry.cget('text')
                hastext = text != ""
                text = "Some Entry" if not hastext else ""
                entry.configure(text=text)

            case 'scrollx':
                bvar: BooleanVar = args[0]
                entry.configure(scrollx=bvar.get())

    frame = ttk.Frame(padding='4')
    frame.pack(fill='x')

    entry = ExEntry(frame, scrollx=True, text="Some Entry")
    entry.pack()

    # Checkbutton that controls the label
    cb = ttk.Checkbutton(frame, text='Label', variable=BooleanVar(value=True),
                         command=lambda: _callback_checkbutton(entry, 'label'))
    cb.pack()

    # Checkbutton that controls the scrollbar
    bvar = BooleanVar(value=True)
    cb = ttk.Checkbutton(frame, text='X Scroll', variable=bvar,
                         command=lambda: _callback_checkbutton(entry, 'scrollx', bvar))
    cb.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
