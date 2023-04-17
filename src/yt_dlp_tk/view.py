# Interface class, the View of MVP.

from .yt_funcs.core import VideoInfo
from .utils import attr_dict
from .interface import ExEntry, ExTree
from .protocols import Presenter
from tkinter import ttk, constants as tkconst
from dataclasses import dataclass
import tkinter as tk

@dataclass
class Column:
    """Column specifier."""

    column: str
    heading: str
    width: int = 200

    def as_tuple(self) -> tuple[str, str, int]:
        """Get the fields as a tuple."""
        return self.column, self.heading, self.width

class YtdlptkInterface(tk.Tk):
    def create_interface(self, presenter: Presenter) -> None:
        widgets = attr_dict()
        self.widgets = widgets

        # Global frame
        frame = ttk.Frame()
        frame.pack(fill=tkconst.BOTH, expand=True)
        widgets.frMain = frame

        # Tabbed notebook widget
        nb = ttk.Notebook(widgets.frMain)
        nb.pack(fill=tkconst.BOTH, expand=True)

        # 'Download' frame
        frame = ttk.Frame(nb)
        widgets.frDownloadVideos = frame

        entry = ExEntry(frame, scrollx=True, text="URL", width=100)
        entry.pack()
        widgets.enURL = entry

        button = ttk.Button(frame, text="Get Video Info",
                            command=presenter.get_video_info)
        button.pack()
        widgets.btSearch = button

         # Video field labels
        subframe = ttk.Frame(frame)
        subframe.pack()
        for i, elt in enumerate([("Title", 'lbTitle'), ("Length", "lbLength"),
                                 ("Age Restricted", "lbAgegate")]):
            text, widget = elt
            ttk.Label(subframe, text=text, anchor=tkconst.E, padding="0 0 8")\
               .grid(row=i, column=0, sticky='w')

            label = ttk.Label(subframe, anchor=tkconst.CENTER, text=("." * 75),
                              width=100, relief=tkconst.SUNKEN)
            label.grid(row=i, column=1, sticky='w')
            widgets[widget] = label

         # Treeview
        COLUMNS = [
            Column('Cformat', "Format"),
            Column('Cextension', "Extension"),
            Column('Cresolution', "Resolution"),
            Column('Crate', "Sample Rate/Fps"),
            Column('Csize', "File Size"),
            Column('Cbitrate', "Average Bitrate")
        ]
        tree = ExTree(frame, show='headings', scrolly=True,
                      columns=[c.as_tuple() for c in COLUMNS],
                      height=20)
        tree.pack()
        widgets.trFormats = tree

        # Add frames to notebook
        nb.add(widgets.frDownloadVideos, text="Video Downloader")

    @property
    def url(self) -> str:
        """URL."""
        entry: ExEntry = self.widgets.enURL
        return entry.get()

    def update_video_info(self, info: VideoInfo):
        widgets = self.widgets

        label: ttk.Label = widgets.lbTitle
        label.config(text=info.title)

        label = widgets.lbLength
        label.config(text=str(info.duration))

        label = widgets.lbAgegate
        label.config(text=str(info.age_limit >= 18))

        tree: ExTree = widgets.trFormats
        formats = info.formats
        
