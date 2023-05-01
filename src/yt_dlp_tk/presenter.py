from __future__ import annotations
from typing import TYPE_CHECKING
from .logging import get_logger, add_handler
from .protocols import Model, View
from .interface.console import ConsoleWindow

if TYPE_CHECKING:
    from typing import Any

class Presenter:
    def __init__(self, model: Model, view: View) -> None:
        logger = get_logger('backend')

        logger.info("Initializing backend...")

        self.model = model
        logger.debug("Model initialized.")
        self.view = view
        self.view.create_interface(self)
        logger.debug("Interface created.")

    def run(self) -> None:
        self.view.mainloop()

    def get_video_info(self) -> None:
        logger = get_logger('backend.youtube')

        logger.info("Retrieving info for %s.", self.view.url)

        result = self.model.get_video_info(self.view.url)
        if result.ok is not None:
            logger.info("Retrieve info for video.")
            info = result.ok
            self.view.update_video_info(info)

    def download_video(self) -> None:
        self.model.download_video(
            self.view.url,
            self.view.format,
            ConsoleWindow.show()
        )
