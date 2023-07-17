"""Model. Check the protocol for documentation."""

from __future__ import annotations
from typing import TYPE_CHECKING
from .utils import Result
from jsnake.logging import get_logger
from .yt_funcs.core import extract_video_info, download_video, VideoInfo, YTErrors
from yt_dlp.utils import DownloadError
from .data import zipped_info, Settings
from pathlib import Path
from configparser import ConfigParser, MissingSectionHeaderError
from PIL import Image

if __debug__:
    from ._debug.pickled_image import PICKLED_IMAGE

import gzip, platformdirs as platform, validators, requests

if TYPE_CHECKING:
    from typing import Any, Literal
    from .protocols import CustomLogger

class Model:
    CONFIGFILE = "config.ini"

    def __init__(self):
        self.video_info: VideoInfo | None = None
        self.images: dict[str, Image.Image] = {}

    def get_video_info(self, url: str) -> Result[None, YTErrors] | Result[VideoInfo, YTErrors]:
        if url.lower() == 'zipped':
            info_bytes = gzip.decompress(zipped_info)
            code = compile(info_bytes, __file__, 'eval')
            info_dict = eval(code)
            assert isinstance(info_dict, dict), type(info_dict)

            self.video_info = VideoInfo.create(info_dict)

            return Result(self.video_info, YTErrors.OK)

        try:
            self.video_info = extract_video_info(url)
        except DownloadError:
            return Result(None, YTErrors.DOWNLOADERROR)

        return Result(self.video_info, YTErrors.OK)

    def cleanup(self):
        self.clear_image_cache()

    def clear_video_info(self):
        self.video_info = None

    def download_video(self, url: str, format_: str, logger: CustomLogger, **kw: Any):
        download_video(url, format_, logger, **kw)

    def _get_platform_user_directory(self, type_: Literal["config"]) -> Path:
        """
        Get the platform-specific directory for TYPE_.

        TYPE_ can be one of:
            * config = configuration directory
        """
        d = Path()
        ds = ""

        if type_ == "config":
            d = platform.user_config_path("yt-dlp-tk", False)
            ds = str(d)

        assert not ds.isspace() and bool(ds), f"invalid path: {ds}"
        return d

    ## Image loading

    def load_image(self, img_path: str | Path, verify=False) -> Image.Image:
        spath = str(img_path)

        # Return image if it is cached
        if spath in self.images:
            return self.images[spath]

        if __debug__:
            if spath == "pickled":
                # DEBUG: Load a pickled image to test image loading
                import pickle
                img = pickle.loads(PICKLED_IMAGE)
                self.images['pickled'] = img
                return img

        if validators.url(spath): # pyright: ignore
            # Is a URL, stream image from web
            response = requests.get(spath, stream=True)
            response.raise_for_status()

            with Image.open(response.raw) as img:
                img.load()
        else:
            # Is a filesystem path, load from file
            if verify:
                # Verify image integrity
                Image.open(spath).verify()

            with Image.open(spath) as img:
                img.load()

        # Add image to cache
        self.images[str(spath)] = img

        return img

    def clear_image_cache(self):
        get_logger('backend.data').info("Clear image cache.")
        self.images.clear()

    # Settings
    #

    def read_settings(self):
        logger = get_logger('backend.data', stream=False)

        config_file = self._get_platform_user_directory("config") / self.CONFIGFILE
        logger.debug("Set configuration file to %s.", config_file)

        default_settings = Settings(Path(".").resolve())

        # Use the default settings in cases where the config file doesn't exist
        if not config_file.exists():
            logger.info("Configuration file does not exist. Using default settings.")
            self.settings = default_settings
            logger.debug("Settings:\n%s", self.settings)
            return

        # Read the configuration file
        config = ConfigParser()
        config.read_file(open(config_file, 'rt'))
        logger.debug("Loaded configuration file.")

        # Option: 'directory/download_path'
        download_path = config.get('directory', 'download_path', fallback=None)
        if download_path is None:
            logger.warn("Missing option 'directory/download_path'. Using default.")
            download_path = default_settings.download_path
        else:
            download_path = Path(download_path)

        self.settings = Settings(download_path)

        logger.debug("Settings:\n%s", self.settings)

    def save_settings(self, settings: Settings):
        logger = get_logger('backend.data', stream=False)

        config_file = self._get_platform_user_directory("config") / self.CONFIGFILE
        logger.debug("Set configuration file to %s.", config_file)

        # Create directory if it does not exist
        if not config_file.parent.exists():
            config_file.parent.mkdir(parents=True)

        # Create and initialize config file parser
        cnf = ConfigParser()
        cnf['directory'] = {
            'download_path': str(settings.download_path)
        }

        # Write config data to file
        try:
            with open(config_file, 'w') as fd:
                cnf.write(fd, True)
                logger.info("Wrote config to %s.", config_file)
        except Exception as exc:
            logger.error("Failed to write %s due to this exception: ", config_file, exc_info=exc)
