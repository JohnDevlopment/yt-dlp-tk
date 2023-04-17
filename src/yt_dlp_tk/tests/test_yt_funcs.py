# from ..yt_funcs import core as yt_funcs_core
from ..yt_funcs.core import Format, FormatType, Duration, YoutubeDL, extract_video_info
from ..utils import get_env
from pathlib import Path
from typing import Any, cast
import pytest, pickle

DurationExpectedType = tuple[list[int] | None, str]

# Functions to parse a URL and cache it

@pytest.fixture
def info_json() -> dict[str, Any]:
    url = get_env('YTDLPTK_TEST_URL')
    assert url is not None, "Please define 'YTDLPTK_TEST_URL' in the environment."

    res: dict[str, Any] = {}

    pickle_file = Path(__file__).parent / 'info-json.pickle'

    if pickle_file.exists():
        # Load the cached info dictionary
        with pickle_file.open('rb') as fd:
            res = pickle.load(fd)

        assert isinstance(res, dict)
        assert res['webpage_url'] == url, f"{url!r} does not match {res['webpage_url']!r}"

        return res

    # Get the info dictionary for the URL and cache it
    res = extract_video_info(url, True)
    with pickle_file.open('wb') as fd:
        pickle.dump(res, fd)

    return res

###

class TestClasses:
    @pytest.mark.parametrize("duration,expected", [
        (
            [0, 1, 8],
            (None, "1:08")
        ),
        (
            70,
            ([0, 1, 10], "1:10")
        ),
        (
            [1, 2, 30],
            (None, "1:02:30")
        ),
        (
            3750,
            ([1, 2, 30], "1:02:30")
        ),
        (
            30,
            ([0, 0, 30], "30")
        )
    ])
    def test_Duration(self, duration: list[int] | int,
                      expected: DurationExpectedType):
        if isinstance(duration, list):
            d = Duration(*duration)
        else:
            d = Duration.convert(duration)

        if not isinstance(duration, list):
            duration = [d.hours, d.minutes, d.seconds]

        exp_dur = cast(list[int], expected[0] or duration)

        assert d.hours == exp_dur[0]
        assert d.minutes == exp_dur[1]
        assert d.seconds == exp_dur[2]

        assert str(d) == expected[1]

    # def test_VideoInfo(self):
    #     # TODO: finish this test
    #     vi = VideoInfo(False, "...", "No Title", 0,
    #                    Duration(0, 1, 10), "")

    @pytest.mark.parametrize("dct,expected", [
        (
            {
                'vcodec': 'h264',
                'acodec': 'none',
                'format': '598 - 256x144 (144p)',
                'vbr': 34.83,
                'tbr': 34.83,
                'fps': 25
            },
            ('h264', 34.83)
        ),
        (
            {
                'vcodec': 'none',
                'acodec': 'opus',
                'asr': 48000,
                'abr': 62.699,
                'format': '250 - audio only (low)'
            },
            ('opus', 62.699)
        ),
        (
            {
                'format': 'sb2 - 48x27 (storyboard)',
                'vcodec': 'none',
                'acodec': 'none',
            },
            ('unknown', 0.0)
        ),
        (
            {
                'format': '300 - 640x480',
                'vcodec': 'h264',
                'acodec': 'opus',
                'asr': 48000,
                'abr': 58.09,
                'vbr': 60.02,
                'tbr': 58.09,
                'fps': 25
            },
            ('h264/opus', 58.09)
        )
    ])
    def test_Format(self, dct: dict[str, Any], expected: tuple[str, float]):
        import math

        fmt = Format.create(dct)
        codecs, br = expected

        assert fmt.codecs == codecs
        assert math.isclose(fmt.bitrate, br)

def test_info_json(monkeypatch: pytest.MonkeyPatch, info_json: dict[str, Any]):
    def _extract_video_info(self, url, download): # pyright: ignore
        return info_json

    assert get_env('YTDLPTK_TEST_URL') is not None

    monkeypatch.setattr(YoutubeDL, 'sanitize_info', lambda x: x)
    monkeypatch.setattr(YoutubeDL, 'extract_info', _extract_video_info)

    assert isinstance(extract_video_info("...", True), dict)

    info = extract_video_info("...")
    # TODO: finish this test
