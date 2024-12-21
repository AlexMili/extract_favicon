import pytest
from PIL import Image

import extract_favicon
from extract_favicon import main_async as ef_async
from extract_favicon.main import Favicon


@pytest.fixture(scope="function")
def favicons():
    return {
        Favicon(
            url="https://www.python.org/static/apple-touch-icon-144x144-precomposed.png",
            format="png",
            width=144,
            height=144,
        ),
        Favicon(
            url="https://www.python.org/static/apple-touch-icon-114x114-precomposed.png",
            format="png",
            width=114,
            height=114,
        ),
        Favicon(
            url="https://www.python.org/static/metro-icon-144x144.png",
            format="png",
            width=144,
            height=144,
        ),
        Favicon(
            url="https://www.python.org/static/favicon.ico",
            format="ico",
            width=0,
            height=0,
        ),
        Favicon(
            url="https://www.python.org/static/apple-touch-icon-precomposed.png",
            format="png",
            width=0,
            height=0,
        ),
        Favicon(
            url="https://www.python.org/static/apple-touch-icon-72x72-precomposed.png",
            format="png",
            width=72,
            height=72,
        ),
    }


def test_base64(base64_img):
    fav = Favicon(base64_img, format=None, width=0, height=0)
    favicons = extract_favicon.download([fav])
    assert len(favicons) == 1
    assert favicons[0].url == fav.url
    assert favicons[0].format == "png"
    assert favicons[0].http is None
    assert favicons[0].valid is True
    assert isinstance(favicons[0].image, Image.Image) is True
    assert favicons[0].width == 1
    assert favicons[0].height == 1


@pytest.mark.asyncio
async def test_base64_async(base64_img):
    fav = Favicon(base64_img, format=None, width=0, height=0)
    favicons = await ef_async.download([fav])
    assert len(favicons) == 1
    assert favicons[0].url == fav.url
    assert favicons[0].format == "png"
    assert favicons[0].http is None
    assert favicons[0].valid is True
    assert isinstance(favicons[0].image, Image.Image) is True
    assert favicons[0].width == 1
    assert favicons[0].height == 1


def test_svg(svg_url):
    fav = Favicon(svg_url, format=None, width=0, height=0)
    favicons = extract_favicon.download([fav])
    assert len(favicons) == 1
    assert favicons[0].format == "svg"
    assert favicons[0].url == fav.url
    assert favicons[0].http.final_url == fav.url
    assert favicons[0].valid is True
    assert isinstance(favicons[0].image, bytes) is True
    assert favicons[0].width == 900
    assert favicons[0].height == 600


@pytest.mark.asyncio
async def test_svg_async(svg_url):
    fav = Favicon(svg_url, format=None, width=0, height=0)
    favicons = await ef_async.download([fav])
    assert len(favicons) == 1
    assert favicons[0].format == "svg"
    assert favicons[0].url == fav.url
    assert favicons[0].http.final_url == fav.url
    assert favicons[0].valid is True
    assert isinstance(favicons[0].image, bytes) is True
    assert favicons[0].width == 900
    assert favicons[0].height == 600


def test_gif(gif_url):
    fav = Favicon(gif_url, format=None, width=0, height=0)
    favicons = extract_favicon.download([fav])
    assert len(favicons) == 1
    assert favicons[0].format == "gif"
    assert favicons[0].url == fav.url
    assert favicons[0].http.final_url == fav.url
    assert favicons[0].valid is True
    assert isinstance(favicons[0].image, Image.Image) is True
    assert favicons[0].width == 500
    assert favicons[0].height == 200


@pytest.mark.asyncio
async def test_gif_async(gif_url):
    fav = Favicon(gif_url, format=None, width=0, height=0)
    favicons = await ef_async.download([fav])
    assert len(favicons) == 1
    assert favicons[0].format == "gif"
    assert favicons[0].url == fav.url
    assert favicons[0].http.final_url == fav.url
    assert favicons[0].valid is True
    assert isinstance(favicons[0].image, Image.Image) is True
    assert favicons[0].width == 500
    assert favicons[0].height == 200


@pytest.mark.parametrize(
    "mode,expected_len",
    [("all", 6), ("largest", 1), ("smallest", 1)],
    ids=["All mode", "Largest mode", "Smallest mode"],
)
def test_mode(favicons, mode, expected_len):
    favs = extract_favicon.download(favicons, mode=mode)
    assert len(favs) == expected_len


@pytest.mark.parametrize(
    "mode,expected_len",
    [("all", 6), ("largest", 1), ("smallest", 1)],
    ids=["All mode", "Largest mode", "Smallest mode"],
)
@pytest.mark.asyncio
async def test_mode_async(favicons, mode, expected_len):
    favs = await ef_async.download(favicons, mode=mode)
    assert len(favs) == expected_len
