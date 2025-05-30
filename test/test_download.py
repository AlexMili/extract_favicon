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


@pytest.mark.parametrize(
    "url,is_valid",
    [("data:image/png;base64,", False), ("data:;base64,", False), ("data:", False)],
    ids=["No img data", "No format data", "Only data"],
)
def test_base64_wrong(url, is_valid):
    fav = Favicon(url, format=None, width=0, height=0)
    fav = extract_favicon.loader._load_base64_img(fav)
    assert fav.url == fav.url
    assert fav.format is None
    assert fav.http is None
    assert fav.valid is is_valid
    assert fav.image is None
    assert fav.width == 0
    assert fav.height == 0


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


def test_generate_default():
    url = "https://www.trustlist.ai/"
    favicon = extract_favicon.generate_favicon(url)

    assert favicon is not None
    assert favicon.format == "svg"
    assert favicon.reachable is True
    assert favicon.valid is True
    assert favicon.width == 100
    assert favicon.height == 100


@pytest.mark.parametrize(
    "url,strategy,img_format,width,height",
    [
        (
            "https://www.trustlist.ai/",
            ["content", "duckduckgo", "google", "generate"],
            "png",
            300,
            300,
        ),
        ("https://www.trustlist.ai/", ["generate"], "svg", 100, 100),
        ("https://www.trustlist.ai/", ["duckduckgo"], "png", 300, 300),
        ("https://www.trustlist.ai/", ["google"], "png", 256, 256),
        (
            "https://somerandometld.trustlist.ai/",
            ["content", "duckduckgo", "google", "generate"],
            "svg",
            100,
            100,
        ),
    ],
    ids=[
        "Default strategy",
        "Gen first strat",
        "Duckduckgo first strat",
        "Google first strat",
        "Default strategy unknown domain",
    ],
)
def test_best_favicon(url, strategy, img_format, width, height):
    favicon = extract_favicon.get_best_favicon(url, strategy=strategy)

    assert favicon is not None
    assert favicon.format == img_format
    assert favicon.reachable is True
    assert favicon.valid is True
    assert favicon.width == width
    assert favicon.height == height
