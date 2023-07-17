from __future__ import annotations
from ..utils import get_env
from ..model import Model
import pytest, os, validators

def test_load_image():
    # Get filesystem path to a thumbnail
    imgpath = get_env('YTDLPTK_TEST_THUMBPATH')
    assert imgpath is not None, "env 'YTDLPTK_TEST_THUMBPATH' is undefined"

    # Get URL to a thumbnail
    url = get_env('YTDLPTK_TEST_THUMBURL')
    assert url is not None, "env 'YTDLPTK_TEST_THUMBURL' is undefined"
    assert validators.url(url), f"'{url}' is not a valid URL" # pyright: ignore

    model = Model()

    # Load image from filesystem
    img = model.load_image(imgpath, True)
    seq = img.getdata()
    assert len(seq) > 0

    # Load image from web
    img = model.load_image(url, True)
    seq = img.getdata()
    assert len(seq) > 0
