from __future__ import annotations
from typing import TYPE_CHECKING
from .logging import get_logger, add_handler
from .protocols import Model, View
from .interface.console import ConsoleWindow

if TYPE_CHECKING:
    from typing import Any

class Presenter:
    def __init__(self, model: Model, view: View) -> None:
        self.model = model
        self.view = view
        self.view.create_interface(self)

        # Logger used for Youtube downloads
        console = ConsoleWindow.show()
        self.logger = get_logger('backend.youtube', stream=False)
        add_handler(self.logger, 'stream', stream=console)
        console.close()

    def run(self) -> None:
        self.view.mainloop()

    def get_video_info(self) -> None:
        result = self.model.get_video_info(self.view.url)
        if result.ok is not None:
            info = result.ok
            self.view.update_video_info(info)

    def download_video(self) -> None:
        ConsoleWindow.show()
        self.model.download_video(
            self.view.url,
            self.view.format,
            self.logger
        )
