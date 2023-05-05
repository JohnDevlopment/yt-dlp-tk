"""Youtube functions via `yt-dlp`."""

from __future__ import annotations
from yt_dlp import YoutubeDL, postprocessor
from ..logging import get_logger
from ..utils import ErrorEnum, unique
from ..protocols import CustomLogger
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, overload
import math

if TYPE_CHECKING:
    from typing import Any, Type, Literal
    from typing_extensions import Self

@unique
class YTErrors(ErrorEnum):
    """Youtube-related errors."""

    OK = 0
    DOWNLOADERROR = 1

@dataclass
class Chapter:
    """A representation of a chapter."""

    start_time: int
    end_time: int
    title: str

@dataclass
class Duration:
    """A representation of a time length."""

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

@dataclass
class Filesize:
    """A representation of a file size."""

    size: float
    unit: Literal['b', 'kb', 'mb', 'gb']
    raw_byte_size: float
    approximate: bool

    def __str__(self) -> str:
        return "{}{}{}".format(
            "~" if self.approximate else "",
            str(self.size),
            " " + self.unit
        )

    @classmethod
    def create(cls, value: float, approximate: bool=False) -> Filesize:
        """Return a Filesize by converting VALUE bytes."""
        raw_size = value
        suffixes = ('b', 'kb', 'mb', 'gb')
        i = 0
        while value > 1024.0:
            value /= 1024.0
            i += 1

        return cls(round(value, 2), suffixes[i], raw_size, approximate)

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
    filesize: Filesize

    @classmethod
    def create(cls: Type[Format], _format: dict[str, Any], /) -> Format:
        """
        Create a Format object based on the fields in _FORMAT.

        _FORMAT needs:
            * tbr
            * format_id
            * One of
                * filesize
                * filesize_approx
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

        # Get the file size
        size: float = _format.get('filesize') or 0.0
        if size > 0.0:
            kw['filesize'] = Filesize.create(size)
        else:
            size = _format.get('filesize_approx', 0.0)
            kw['filesize'] = Filesize.create(size, True)

        return cls(**kw)

@dataclass(slots=True)
class VideoInfo:
    title: str
    url: str
    is_live: bool
    age_limit: int
    duration: Duration
    formats: list[Format]
    _live_status: str
    has_chapters: bool = False
    chapters: list[Chapter] = field(default_factory=list)

    @classmethod
    def create(cls, opts: dict[str, Any]) -> Self:
        import itertools

        kw: dict[str, Any] = {}

        live_status: str = opts['live_status']
        kw.update(
            _live_status=live_status,
            is_live=(live_status == "is_live"),
            url=opts['webpage_url'],
            title=opts['title'],
            duration=Duration.convert(opts.get('duration', 0)),
            age_limit=opts['age_limit']
        )

        # Get a list of formats associated with the video
        gen1 = (Format.create(dct) for dct in opts['formats'])
        it = itertools.filterfalse(
            lambda fmt: fmt.fmttype == FormatType.OTHER, gen1)
        kw['formats'] = list(it)

        # Check if the video has chapters
        chapters = opts.get('chapters', [])
        if chapters:
            kw['has_chapters'] = True
            kw['chapters'] = [
                Chapter(**ch)
                for ch in chapters
            ]

        return cls(**kw)

    def __str__(self) -> str:
        return f"{self.title} | {self.url}, duration: {self.duration}, live: {self.is_live}, " \
            + f"age restriction: {self.age_limit or None}, {len(self.formats)} formats"

def download_video(url: str, format_: str, yt_logger: CustomLogger, *,
                   chapters: Literal['none', 'embed']='none'):
    """
    Download the video from URL in the given FORMAT_.

    Raises yt_dlp.utils.DownloadError if
    an error occurs during download. It
    is aliased as Yt_DownloadError here.

    **KW contains keyword options supported
    by yt_dlp.YoutubeDL.
    """

    logger = get_logger('backend.yt', stream=False)

    logger.info("Downloading video from %s.", url)

    opts: dict[str, Any] = {
        'quiet': False,
        'dump_single_json': False,
        'format': format_,
        'age_limit': 18,
        'restrictfilenames': True,
        'simulate': False,
        'logger': yt_logger
    }

    logger.debug("Initial options: %r", opts)

    with YoutubeDL(opts) as ydl:
        # Post-processing: chapters
        match chapters:
            case 'embed':
                ydl.add_post_processor(
                    postprocessor.FFmpegMetadataPP(ydl))
                logger.debug("Embed chapters.")
            case 'split':
                ydl.add_post_processor(
                    postprocessor.FFmpegSplitChaptersPP(ydl))
                logger.debug("Split video into chapters.")
            case 'none':
                pass
            case arg:
                valid_chapters = ['none', 'embed', 'split']
                if chapters not in valid_chapters:
                    valid_chapters = ', '.join(valid_chapters)
                    raise ValueError(f"invalid 'chapters' {arg!r}, can be one of {valid_chapters}")

        logger.debug("Downloading video...")

        ydl.download([url])

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
