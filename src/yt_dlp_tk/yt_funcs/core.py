"""Youtube functions via `yt-dlp`."""

from __future__ import annotations
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from ..logging import get_logger
from ..utils import Result, ErrorEnum, unique
from enum import Enum
# from yt_dlp.postprocessor.common import PostProcessor
from dataclasses import dataclass
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from typing import Any, Type
    from typing_extensions import Self

@unique
class YTErrors(ErrorEnum):
    """Youtube-related errors."""

    OK = 0
    DOWNLOADERROR = 1

@dataclass
class Duration:
    hours: int
    minutes: int
    seconds: int

    @classmethod
    def convert(cls, time: int) -> Self:
        """Convert TIME into a Duration object."""
        hours = minutes = 0

        seconds = time
        while seconds >= 60:
            seconds -= 60
            minutes += 1

            if minutes == 60:
                minutes -= 60
                hours += 1

        return cls(hours, minutes, seconds)

    def __str__(self) -> str:
        h, m, s = self.hours, self.minutes, self.seconds
        if h > 0:
            return f"{h}:{m:02}:{s:02}"
        elif m > 0:
            return f"{m}:{s:02}"
        return str(s)

@unique
class FormatType(Enum):
    VIDEO = 'video'
    AUDIO = 'audio'
    VIDEOAUDIO = 'audio/video'
    OTHER = 'other'

@dataclass(slots=True)
class Format:
    fmtname: str
    fmtid: str
    fmttype: FormatType
    codecs: str
    bitrate: float
    samplerate: float
    framerate: float
    resolution: str
    width: int
    height: int

    @classmethod
    def create(cls: Type[Format], _format: dict[str, Any], /) -> Format:
        """
        Create a Format object based on the fields in _FORMAT.

        _FORMAT needs:
            * tbr
            * format_id
          If Audio Format:
            * acodec
            * asr
            * abr
          If Video Format:
            * vcodec
            * fps
            * vbr
            * resolution
            * width
            * height
        """
        vc = _format['vcodec'] if _format['vcodec'] != 'none' else ''
        ac = _format['acodec'] if _format['acodec'] != 'none' else ''

        # Format type
        if vc and ac:
            format_type = FormatType.VIDEOAUDIO
        elif vc:
            format_type = FormatType.VIDEO
        elif ac:
            format_type = FormatType.AUDIO
        else:
            format_type = FormatType.OTHER

        sr = fr = br = 0.0
        ru = ''
        fn: str = _format['format']

        # Format name
        match format_type:
            case FormatType.VIDEOAUDIO:
                codecs = f"{vc}/{ac}"
                fr: int | float = _format['fps'] or 0
                sr: int | float = _format['asr'] or 0
                br: int | float = _format['tbr'] or 0
                ru = 'Hz'

            case FormatType.VIDEO:
                codecs = vc
                fr: int | float = _format['fps'] or 0
                br: int | float = _format['vbr'] or 0

            case FormatType.AUDIO:
                codecs = ac
                sr: int | float = _format['asr'] or 0
                br: int | float = _format['abr'] or 0
                ru = 'Hz'

            case _:
                codecs = "unknown"

        kw: dict[str, Any] = {
            'fmtname': fn,
            'fmttype': format_type,
            'bitrate': br,
            'samplerate': sr,
            'framerate': fr,
            'codecs': codecs,
            'width': _format.get('width', 0),
            'height': _format.get('height', 0),
            'resolution': _format.get('resolution', ''),
            'fmtid': _format['format_id']
        }

        return cls(**kw)

@dataclass
class VideoInfo:
    title: str
    url: str
    is_live: bool
    age_limit: int
    duration: Duration
    formats: list[Format]

    _live_status: str

    @classmethod
    def create(cls, opts: dict[str, Any]) -> Self:
        import itertools

        kw: dict[str, Any] = {}

        live_status: str = opts['live_status']
        kw.update(_live_status=live_status,
                  is_live=(live_status == "is_live"),
                  url=opts['webpage_url'], title=opts['title'],
                  duration=Duration.convert(opts.get('duration', 0)),
                  age_limit=opts['age_limit'])

        # Get a list of formats associated with the video
        gen1 = (Format.create(dct) for dct in opts['formats'])
        it = itertools.filterfalse(
            lambda fmt: fmt.fmttype == FormatType.OTHER, gen1)
        kw['formats'] = list(it)

        return cls(**kw)

    def __str__(self) -> str:
        return f"{self.title} | {self.url}, duration: {self.duration}, live: {self.is_live}, " \
            + f"age restriction: {self.age_limit or None}, {len(self.formats)} formats"

@overload
def extract_video_info(url: str) -> VideoInfo:
    ...

@overload
def extract_video_info(url: str, json: bool) -> dict[str, Any]:
    ...

def extract_video_info(url, json=False):
    """
    Get an info dictionary for the given URL.

    If JSON is true, returns a dictionary.
    Otherwise, returns a VideoInfo object.

    Raises yt_dlp.utils.DownloadError if
    an error occurs during download. It
    is aliased as Yt_DownloadError here.
    """
    logger = get_logger('yt', stream=True)

    opts: dict[str, Any] = {
        'quiet': True,
        'dump_single_json': True,
        'logger': logger,
        'age_limit': 18
    }

    logger.info("Extracting info for %s", url)
    with YoutubeDL(opts) as ydl:
        info = YoutubeDL.sanitize_info(
            ydl.extract_info(url, download=False))
    assert isinstance(info, dict)

    logger.info("Extracted info for video ID")

    if json:
        return info
    return VideoInfo.create(info)
