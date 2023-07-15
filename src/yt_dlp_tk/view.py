# Interface class, the View of MVP.

from __future__ import annotations
from .yt_funcs.core import VideoInfo, FormatType
from .utils import InvalidSignal, attr_dict
from jsnake.interface.widgets import ExEntry, ExTree
from jsnake.interface.utils import TkBusyCommand, InState, StringVar
from .protocols import Presenter
from jsnake.logging import get_logger
from .data import Settings
from tkinter import ttk, constants as tkconst
from dataclasses import dataclass
from typing import cast
from pathlib import Path
import tkinter as tk, time

class Statusbar(ttk.Frame):
    """A statusbar."""

    def __init__(self, master) -> None:
        super().__init__(master, relief=tk.SUNKEN)
        self.label = ttk.Label(self)
        self.label.pack(side=tk.LEFT)
        self.pack(fill=tk.X, side=tk.BOTTOM)
        self.timer = ""

    def set(self, text: str, timer: float | None=None) -> None:
        """
        Set the message.

        If TIMER is a number greater than zero, a timer is set,
        after which the message is cleared.
        """
        # This also stops the timer, if one is active
        self.clear()

        # Set the label text
        self.label.config(text=text)

        if timer is not None and timer > 0.0:
            # Calculate milliseconds
            seconds = int(timer * 1000.0)
            # Set the timer
            self.timer = self.after(seconds, self.__on_timer_cleared)

    def clear(self) -> None:
        """Clear the message."""
        self.label.config(text="")

        # Timer is activate
        if self.timer:
            # Cancel timer
            self.after_cancel(self.timer)

            # Invalidate timer identifier
            self.timer = ""

    def __on_timer_cleared(self) -> None:
        # Timer has cleared
        self.timer = ""
        self.clear()

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

    def __init__(self, screen_name: str | None=None, basename: str | None=None,
                 class_name: str='Tk', use_tk: bool=True, sync: bool=False,
                 use: str | None=None):
        super().__init__(screen_name, basename, class_name, use_tk, sync, use)
        self.title("Yt-dlp Tk Interface")

    def create_interface(self, presenter: Presenter) -> None:
        # Register the exit hook
        self.protocol("WM_DELETE_WINDOW", presenter.shutdown)

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

        def _copy_label(event: tk.Event[ttk.Label]) -> None:
            # Copies the contents of label to the clipboard
            widget = event.widget

            # Get label text
            text: str = widget.cget('text')

            # Replace the clipboard contents with the text
            widget.clipboard_clear()
            widget.clipboard_append(text)

            statusbar.set("Label copied", 3)

        LABELS: list[tuple[str, str]] = [
            ("Title", 'lbTitle'),
            ("Length", "lbLength"),
            ("Age Restricted", "lbAgegate"),
            ("Has Chapters", "lbChaptered")
        ]

        for i, elt in enumerate(LABELS):
            # Text label and widget
            text, widget = elt

            # Left label that shows the name of the field
            ttk.Label(subframe, text=text, anchor=tkconst.E, padding="0 0 8")\
               .grid(row=i, column=0, sticky='w')

            # Label that contains the field's value
            label = ttk.Label(subframe, anchor=tkconst.CENTER, text=self.DEFAULT_LABEL,
                              width=100, relief=tkconst.SUNKEN)
            # Map the label rightward of the other label
            label.grid(row=i, column=1, sticky='w')

            # Save the label
            widgets[widget] = label

            # Bind right-click to copy past function
            label.bind("<3>", lambda e: _copy_label(e))

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

         # Download options
        subframe = ttk.Frame(frame)
        subframe.pack()

          # Radio buttons: chapters
        var = StringVar(master=frame, name='CHAPTERS', value='none')

           # Define a list of chapter radiobutton widgets
        widgets['chapters'] = []

        rb = ttk.Radiobutton(subframe, variable=var, value='none',
                             text="No chapters", state='disabled')
        rb.grid(row=0, column=0)
        widgets.chapters.append(rb)

        rb = ttk.Radiobutton(subframe, variable=var, value='embed',
                             text="Embed chapters in video", state='disabled')
        rb.grid(row=0, column=1)
        widgets.chapters.append(rb)

        rb = ttk.Radiobutton(subframe, variable=var, value='split',
                             text="Split video into chapters", state='disabled')
        rb.grid(row=0, column=2)
        widgets.chapters.append(rb)

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

        # Define settings frame
        self.__settings_tab()

        # Add frames to notebook
        nb.add(widgets.frDownloadVideos, text="Video Downloader")
        nb.add(self.widgets.frSettings, text="Settings")

        # Create statusbar
        statusbar = Statusbar(widgets.frMain)
        widgets.statusbar = statusbar

        statusbar.set("Interface loaded", 3)

    def cleanup(self):
        pass

    def __settings_tab(self) -> ttk.Frame:
        frame = ttk.Frame()
        frame.pack(fill=tkconst.BOTH, expand=True)
        self.widgets.frSettings = frame

        entry = ExEntry(frame, text="Download Path")
        entry.grid(row=0, column=0)
        self.widgets.enDownloadPath = entry

        # Button that lets the user choose a directory
        def _browse_dir() -> None:
            from tkinter.filedialog import askdirectory
            settings = self.get_settings()
            d = askdirectory(initialdir=str(settings.download_path), parent=frame, title="Choose Download Path")
            if d:
                settings.download_path = Path(d)
                self.update_settings(settings)

        ttk.Button(frame, text="Browse...", command=_browse_dir).grid(row=0, column=1)

        return frame

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

    def get_download_options(self):
        return {
            "chapters": StringVar(name='CHAPTERS').get()
        }

    ###

    # Settings
    #

    def get_settings(self):
        # The download path
        download_path = cast(ExEntry, self.widgets.enDownloadPath).get()
        download_path = Path(download_path)
        if not download_path.exists() or not download_path.exists():
            download_path = Path(".")

        return Settings(
            download_path.resolve()
        )

    def update_settings(self, settings: Settings):
        entry: ExEntry = self.widgets.enDownloadPath
        entry.delete(0, tkconst.END)
        entry.insert(0, str(settings.download_path))

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

        label = widgets.lbChaptered
        label.config(text=str(info.has_chapters))

        # Add formats to the tree
        tree: ExTree = widgets.trFormats
        tree.clear()

        tree.insert('', 'end', text="Audio", open=True, iid='Iaudio')
        tree.insert('', 'end', text="Video", open=True, iid='Ivideo')

        # Enable radio buttons if the video has chapters
        if info.has_chapters:
            for rb in self.widgets.chapters:
                cast(ttk.Radiobutton, rb).state(('!disabled',))

        logger.debug("%d formats", len(info.formats))
        for fmt in info.formats:
            match fmt.fmttype:
                case FormatType.AUDIO:
                    logger.debug("Added format: %s", fmt.fmtname)
                    values = (fmt.fmtid, fmt.fmtname, '', '', fmt.samplerate,
                              str(fmt.filesize), fmt.bitrate)
                    tree.insert('Iaudio', 'end', values=values)

                case FormatType.VIDEO:
                    logger.debug("Added format: %s", fmt.fmtname)
                    values = (fmt.fmtid, fmt.fmtname, '', fmt.resolution, fmt.framerate,
                              str(fmt.filesize), fmt.bitrate)
                    tree.insert('Ivideo', 'end', values=values)

    def clear_video_info(self):
        widgets = self.widgets

        # Reset labels to their default labels
        for temp in ['lbTitle', 'lbLength', 'lbAgegate', 'lbChaptered']:
            label = cast(ttk.Label, widgets[temp])
            label.config(text=self.DEFAULT_LABEL)

        # Clear text from widgets
        # Clear tree widget
        cast(ExTree, widgets.trFormats).clear()
        # Clear video format entry
        entry = cast(ExEntry, widgets.enVideo)
        entry.delete(0, tkconst.END)
        # Clear audio format entry
        entry = cast(ExEntry, widgets.enAudio)
        entry.delete(0, tkconst.END)

        # Reset radiobuttons
        StringVar(name='CHAPTERS').set('none')
        for rb in self.widgets.chapters:
            cast(ttk.Radiobutton, rb).state(('disabled',))

        self.update()
