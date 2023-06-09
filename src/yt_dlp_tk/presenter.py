from __future__ import annotations
from typing import TYPE_CHECKING
from .logging import get_logger, add_handler
from .interface.console import ConsoleWindow

if TYPE_CHECKING:
    from typing import Any
    from .protocols import Model, View

class Presenter:
    def __init__(self, model: Model, view: View):
        logger = get_logger('backend')

        logger.info("Initializing backend...")

        self.model = model
        self.view = view

        # Sets an attribute in Model
        self.model.read_settings()

        # Create the interface and update it with the settings
        self.view.create_interface(self)
        self.view.update_settings(self.model.settings)

        logger.debug("Interface created.")

    def run(self) -> None:
        self.view.mainloop()

    def exit(self):
        logger = get_logger('backend')

        logger.debug("Writing settings to file.")
        settings = self.view.get_settings()
        self.model.save_settings(settings)

        logger.debug("Exiting...")
        self.view.quit()

    def get_video_info(self) -> None:
        logger = get_logger('backend.youtube', stream=False)

        logger.debug("Clear data.")
        self.model.clear_video_info()

        logger.debug("Clear interface.")
        self.view.clear_video_info()

        logger.info("Retrieving info for %s.", self.view.url)
        result = self.model.get_video_info(self.view.url)
        if result.ok is not None:
            logger.info("Retrieved info for video.")
            info = result.ok
            self.view.update_video_info(info)

    def download_video(self) -> None:
        opts = self.view.get_download_options()
        kw = {
            'chapters': opts['chapters']
        }
        self.model.download_video(
            self.view.url,
            self.view.format,
            ConsoleWindow.show(),
            **kw
        )
