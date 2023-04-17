from __future__ import annotations
from typing import TYPE_CHECKING
from .utils import Result
from .yt_funcs.core import extract_video_info, DownloadError as Yt_DownloadError, VideoInfo, YTErrors
from .data import zipped_info
import gzip

if TYPE_CHECKING:
    from typing import Any

class Model:
    def get_video_info(self, url: str) -> Result[None, YTErrors] | Result[VideoInfo, YTErrors]:
        """Get info for the specified URL."""
        if url.lower() == 'zipped':
            info_bytes = gzip.decompress(zipped_info)
            code = compile(info_bytes, __file__, 'eval')
            info_dict = eval(code)
            assert isinstance(info_dict, dict), type(info_dict)

            self.video_info = VideoInfo.create(info_dict)

            return Result(self.video_info, YTErrors.OK)

        try:
            self.video_info = extract_video_info(url)
        except Yt_DownloadError as exc:
            return Result(None, YTErrors.DOWNLOADERROR)

        return Result(self.video_info, YTErrors.OK)
