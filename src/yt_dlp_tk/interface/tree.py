from __future__ import annotations
from tkinter import ttk, constants as tkconst
from .utils import _WidgetMixin, _Column
from ..logging import get_logger
from ..signals import signal, InvalidSignalError
from typing import TYPE_CHECKING, cast
import tkinter as tk

if TYPE_CHECKING:
    from typing import Any
    from .utils import _Widget

class ExTree(ttk.Treeview, _WidgetMixin):
    """
    Extended treeview widget.

    Signals:

        x_scrollbar_changed()
            * The horizontal scrollbar has changed, either
              true if it is enabled or false otherwise

        y_scrollbar_changed(state: bool)
            * The vertical scrollbar has changed, either
              true if it is enabled or false otherwise

        item_doubleclicked(*, region: str, column: str, row: str, element: str)
            * The user has double-clicked the tree. Keyword arguments denoting the
              region ('heading', 'separator', 'tree', 'cell', or 'nothing'); the
              column (#0 being the tree column); the row; and the element, are provided.
    """

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
        """
        logger = self.logger = get_logger('gui.widgets.ExTree', stream=True)

        # Signals
        self.on_x_scrollbar_changed = signal('x_scrollbar_changed', self)
        self.on_x_scrollbar_changed.connect(self)

        self.on_y_scrollbar_changed = signal('y_scrollbar_changed', self)
        self.on_y_scrollbar_changed.connect(self)

        self.on_item_doubleclicked = signal('item_doubleclicked', self)
        self.on_item_doubleclicked.connect(self)

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

        self.bind('<Double-1>', self._eventcb_doubleclicked)

    def _eventcb_doubleclicked(self, event: tk.Event):
        x, y = event.x, event.y
        region = self.identify_region(x, y)
        column = self.identify_column(x)
        row = self.identify_row(y)
        element = self.identify_element(x, y)

        return self.on_item_doubleclicked.emit(region=region, column=column, row=row, element=element)

    def add_root(self, iid: str | None=None, **kw: Any) -> str:
        """Add a root node."""
        root = self.insert('', 0, iid, **kw)
        self.set_meta('_root', root)
        return root

    @property
    def root(self) -> str:
        """The root item."""
        return self.get_meta('root', '')

    def clear(self) -> None:
        """Clear the tree."""
        children = self.get_children()
        self.delete(*children)

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

            case 'item_doubleclicked':
                pass

            case _: # pragma: no cover
                raise InvalidSignalError(sig)

ExTree.override_init_docstring(ttk.Treeview)
