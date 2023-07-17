from __future__ import annotations
from typing import TYPE_CHECKING
from jsnake.logging import get_logger
from .interface.console import ConsoleWindow
from PIL import ImageTk

if TYPE_CHECKING:
    from typing import Any
    from .protocols import Model, View
    from pathlib import Path

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

    def load_image(self, img_path: str | Path):
        img = self.model.load_image(img_path)
        tkimg = ImageTk.PhotoImage(img)

        return tkimg

    def clear_image_cache(self):
        self.model.clear_image_cache()

    def shutdown(self):
        logger = get_logger('backend')

        logger.info("Shutting down backend...")

        logger.debug("Writing settings to file.")
        settings = self.view.get_settings()
        self.model.save_settings(settings)

        self.view.cleanup()
        self.model.cleanup()

        self.view.quit()

    def get_video_info(self) -> None:
        logger = get_logger('backend.youtube', stream=False)

        # View
        logger.debug("Clear interface.")
        self.view.clear_video_info()

        # Model
        logger.debug("Clear data.")
        self.model.clear_video_info()
        self.model.clear_image_cache()

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
