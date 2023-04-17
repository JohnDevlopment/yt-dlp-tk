from __future__ import annotations
from .yt_funcs.core import VideoInfo, YTErrors
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Any
    from .utils import Result

class Presenter(Protocol):
    def __init__(self, model: Model, view: View) -> None:
        ...

    def run(self) -> None:
        ...

    def get_video_info(self) -> None:
        ...

class Model(Protocol):
    def get_video_info(self, url: str) -> Result[None, YTErrors] | Result[VideoInfo, YTErrors]:
        ...

class View(Protocol):
    def mainloop(self) -> None:
        ...

    def create_interface(self, presenter: Presenter) -> None:
        ...

    def update_video_info(self, info: VideoInfo) -> None:
        ...

    @property
    def url(self) -> str:
        ...
