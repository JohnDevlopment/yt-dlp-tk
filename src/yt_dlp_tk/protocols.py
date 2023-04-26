from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Any
    from .utils import Result
    from .yt_funcs.core import VideoInfo, YTErrors

class Presenter(Protocol):
    def __init__(self, model: Model, view: View) -> None: ...

    def run(self) -> None: ...

    def get_video_info(self) -> None: ...

    def download_video(self) -> None: ...

class Model(Protocol):
    def get_video_info(self, url: str) -> Result[None, YTErrors] | Result[VideoInfo, YTErrors]: ...

    def download_video(self, url: str, format_: str, logger: CustomLogger) -> None: ...

class View(Protocol):
    def mainloop(self) -> None: ...

    def create_interface(self, presenter: Presenter) -> None: ...

    def update_video_info(self, info: VideoInfo) -> None: ...

    @property
    def url(self) -> str: ...

    @property
    def format(self) -> str: ...

class CustomLogger(Protocol):
    def debug(self, msg: str, *args: Any):
        """Print message with severity debug."""
        ...

    def info(self, msg: str, *args: Any):
        """Print message with severity info."""
        ...

    def warn(self, msg: str, *args: Any):
        """Print message with severity warn."""
        ...

    def error(self, msg: str, *args: Any):
        """Print message with severity error."""
        ...

    def critical(self, msg: str, *args: Any):
        """Print message with severity critical."""
        ...
