"""Model. Check the protocol for documentation."""

from __future__ import annotations
from typing import TYPE_CHECKING
from .utils import Result
from .yt_funcs.core import extract_video_info, download_video, VideoInfo, YTErrors
from yt_dlp.utils import DownloadError
from .data import zipped_info
import gzip

if TYPE_CHECKING:
    from typing import Any
    from .protocols import CustomLogger

class Model:
    def __init__(self):
        self.video_info: VideoInfo | None = None

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

    def clear_video_info(self):
        self.video_info = None

    def download_video(self, url: str, format_: str, logger: CustomLogger, **kw: Any):
        download_video(url, format_, logger=logger, **kw)
