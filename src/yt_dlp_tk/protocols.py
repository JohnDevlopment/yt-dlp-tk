from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Any
    from .utils import Result
    from .yt_funcs.core import VideoInfo, YTErrors
    from .data import Settings

class Presenter(Protocol):
    def __init__(self, model: Model, view: View) -> None: ...

    def run(self) -> None:
        """Run the program. Enter the main loop."""
        ...

    def get_video_info(self) -> None:
        """Get video info. Calls Model."""
        ...

    def download_video(self) -> None:
        """Download the video. Calls Model."""
        ...

    def exit(self) -> None:
        """Exit the application."""
        ...

class Model(Protocol):
    def get_video_info(self, url: str) -> Result[None, YTErrors] | Result[VideoInfo, YTErrors]:
        """
        Return info for the video located at URL.

        If successful, returns a Result with the Ok value being
        a VideoInfo; otherwise returns a Result with the Err value
        set to a enum of YTErrors.
        """
        ...

    def download_video(self, url: str, format_: str, logger: CustomLogger, **kw: Any) -> None:
        """
        Download the video from URL in the given FORMAT.

        LOGGER is used to log messages directly from yt-dlp.
        """
        ...

    def clear_video_info(self) -> None:
        """Clears video info."""
        ...

    # Methods/properties for saving and loading settings
    #

    def save_settings(self, settings: Settings) -> None:
        """Save settings to config file."""
        ...

    def read_settings(self) -> None:
        """Read the settings from the configuration file."""
        ...

    @property
    def settings(self) -> Settings:
        """Loaded settings."""
        ...

class View(Protocol):
    def mainloop(self) -> None:
        """Main loop for the interface."""
        ...

    def create_interface(self, presenter: Presenter) -> None:
        """
        Create the interface.

        Shall only be called once and before calling View.mainloop().
        """
        ...

    def update_video_info(self, info: VideoInfo) -> None:
        """Update the interface with contents of INFO."""
        ...

    def clear_video_info(self) -> None:
        """Clears video info. Called by Presenter."""
        ...

    @property
    def url(self) -> str:
        """The contents of the URL entry."""
        ...

    @property
    def format(self) -> str:
        """Format specifier."""
        ...

    def get_settings(self) -> Settings:
        """Get the options defined in the settings tab."""
        ...

    def update_settings(self, settings: Settings) -> None:
        """Update the interface with SETTINGS."""
        ...

    def get_download_options(self) -> dict[str, Any]:
        """
        Return options for downloading the video.

        Keys:
            * chapters - {none, split, embed} specifies how
                         to handle video chapters
        """
        ...

    def quit(self) -> None:
        """Exit the interface."""
        ...

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
