# Interface class, the View of MVP.

from __future__ import annotations
from .yt_funcs.core import VideoInfo, FormatType
from .utils import InvalidSignal, attr_dict
from .interface import ExEntry, ExTree
from .interface.utils import TkBusyCommand, InState
from .protocols import Presenter
from .logging import get_logger
from tkinter import ttk, constants as tkconst
from dataclasses import dataclass
from typing import cast
import tkinter as tk, time

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
    DEFAULT_LABEL = "." * 75

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
                            command=lambda: self.get_video_info(button, presenter))
        button.pack()
        widgets.btSearch = button

         # Video field labels
        subframe = ttk.Frame(frame)
        subframe.pack()

        LABELS = [
            ("Title", 'lbTitle'),
            ("Length", "lbLength"),
            ("Age Restricted", "lbAgegate")
        ]

        for i, elt in enumerate(LABELS):
            text, widget = elt
            ttk.Label(subframe, text=text, anchor=tkconst.E, padding="0 0 8")\
               .grid(row=i, column=0, sticky='w')

            label = ttk.Label(subframe, anchor=tkconst.CENTER, text=self.DEFAULT_LABEL,
                              width=100, relief=tkconst.SUNKEN)
            label.grid(row=i, column=1, sticky='w')
            widgets[widget] = label

         # Format field entries
        subframe = ttk.Frame(frame)
        subframe.pack()

        entry = ExEntry(subframe, width=5, text='Video Format')
        entry.pack(side=tkconst.LEFT)
        widgets.enVideo = entry

        entry = ExEntry(subframe, width=5, text='Audio Format')
        entry.pack(side=tkconst.LEFT)
        widgets.enAudio = entry

        ttk.Button(frame, text='Download',
                   command=lambda: self.download_video(presenter))\
           .pack()

         # Treeview
        COLUMNS = [
            Column('Cid', "ID"),
            Column('Cformat', "Format"),
            Column('Cextension', "Extension"),
            Column('Cresolution', "Resolution"),
            Column('Crate', "Sample Rate/Fps"),
            Column('Csize', "File Size"),
            Column('Cbitrate', "Average Bitrate")
        ]

        tree = ExTree(frame, scrolly=True,
                      columns=[c.as_tuple() for c in COLUMNS],
                      displaycolumns=['Cformat', 'Cresolution',
                                      'Crate', 'Csize', 'Cbitrate'],
                      selectmode=tkconst.BROWSE,
                      height=20)

        tree.column("#0", width=150, minwidth=150)
        tree.heading("#0", text="Format Type")
        tree.pack()
        tree.on_item_doubleclicked.connect(self)
        widgets.trFormats = tree

        # Add frames to notebook
        nb.add(widgets.frDownloadVideos, text="Video Downloader")

    def on_notify(self, sig: str, obj: ExTree, *args, **kw: str):
        logger = get_logger('view.signals')

        if sig != 'item_doubleclicked':
            raise InvalidSignal(sig)

        column = kw['column']

        if kw['region'] != 'cell' or column == '#0':
            return

        item = kw['row']
        if item in ['Iaudio', 'Ivideo']:
            return

        tree: ExTree = self.widgets.trFormats

        logger.debug("Selected item %s. Its parent is %s.", item,
                     tree.parent(item))
        logger.debug("Selected column %s.", column)

        # Get list of values from item
        values = tree.item(item, 'values')
        assert values

        # Format type, audio or video
        what = tree.parent(item)[1:].lower()
        assert what in ('audio', 'video')

        fmtid: str = values[0]
        logger.info("Selected %s format %s.", what, fmtid)

        entry: ExEntry = self.widgets.enAudio if what == 'audio' else self.widgets.enVideo
        entry.delete(0, 'end')
        entry.insert(0, fmtid)

    # Properties

    @property
    def url(self) -> str:
        entry: ExEntry = self.widgets.enURL
        return entry.get()

    @property
    def format(self) -> str:
        w = self.widgets
        vf: str = w.enVideo.get()
        af: str = w.enAudio.get()
        return "+".join((vf, af))

    ###

    def get_video_info(self, button: ttk.Button, presenter: Presenter):
        frame = self.widgets.frMain
        with InState(button, ('disabled',)):
            with TkBusyCommand(frame, frame):
                self.update()
                time.sleep(0.5)
                presenter.get_video_info()

    def download_video(self, presenter: Presenter):
        with TkBusyCommand(self.widgets.frMain, self.widgets.frMain):
            self.update()
            time.sleep(0.5)
            presenter.download_video()

    def update_video_info(self, info: VideoInfo):
        """Update the GUI with info about a video."""
        logger = get_logger('view.update')

        logger.info("Updating interface with video info.")
        logger.debug("%s", info)

        widgets = self.widgets

        label: ttk.Label = widgets.lbTitle
        label.config(text=info.title)

        label = widgets.lbLength
        label.config(text=str(info.duration))

        label = widgets.lbAgegate
        label.config(text=str(info.age_limit >= 18))

        # Add formats to the tree
        tree: ExTree = widgets.trFormats
        tree.clear()

        tree.insert('', 'end', text="Audio", open=True, iid='Iaudio')
        tree.insert('', 'end', text="Video", open=True, iid='Ivideo')

        logger.debug("%d formats", len(info.formats))
        for fmt in info.formats:
            match fmt.fmttype:
                case FormatType.AUDIO:
                    logger.debug("Added format: %s", fmt.fmtname)
                    values = (fmt.fmtid, fmt.fmtname, '', '', fmt.samplerate, '', fmt.bitrate)
                    tree.insert('Iaudio', 'end', values=values)

                case FormatType.VIDEO:
                    logger.debug("Added format: %s", fmt.fmtname)
                    values = (fmt.fmtid, fmt.fmtname, '', '', fmt.framerate, '', fmt.bitrate)
                    tree.insert('Ivideo', 'end', values=values)

    def clear_video_info(self):
        widgets = self.widgets

        for temp in ['lbTitle', 'lbLength', 'lbAgegate']:
            label = cast(ttk.Label, widgets[temp])
            label.config(text=self.DEFAULT_LABEL)

        cast(ExTree, widgets.trFormats).clear()

        self.update()
