import pytest
from PIL import Image

import extract_favicon
from extract_favicon.main import Favicon


@pytest.mark.parametrize(
    "url",
    [
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg==",
    ],
    ids=["Base64"],
)
def test_base64(url):
    fav = Favicon(url, None, width=0, height=0)
    favicons = extract_favicon.download([fav])
    assert len(favicons) == 1
    assert favicons[0].original == fav
    assert favicons[0].url.url == fav.url
    assert favicons[0].format == "png"
    assert favicons[0].url.final_url == fav.url
    assert favicons[0].valid is True
    assert isinstance(favicons[0].image, Image.Image) is True
    assert favicons[0].width == 1
    assert favicons[0].height == 1


@pytest.mark.parametrize(
    "url",
    [
        "https://upload.wikimedia.org/wikipedia/commons/c/c3/Flag_of_France.svg",
    ],
    ids=["SVG"],
)
def test_svg(url):
    fav = Favicon(url, None, width=0, height=0)
    favicons = extract_favicon.download([fav])
    assert len(favicons) == 1
    assert favicons[0].original == fav
    assert favicons[0].format == "svg"
    assert favicons[0].url.url == fav.url
    assert favicons[0].url.final_url == fav.url
    assert favicons[0].valid is True
    assert isinstance(favicons[0].image, bytes) is True
    assert favicons[0].width == 900
    assert favicons[0].height == 600


@pytest.mark.parametrize(
    "url",
    [
        "https://www.google.com/logos/doodles/2024/seasonal-holidays-2024-6753651837110333.2-la202124.gif",
    ],
    ids=["Gif"],
)
def test_gif(url):
    fav = Favicon(url, None, width=0, height=0)
    favicons = extract_favicon.download([fav])
    assert len(favicons) == 1
    assert favicons[0].original == fav
    assert favicons[0].format == "gif"
    assert favicons[0].url.url == fav.url
    assert favicons[0].url.final_url == fav.url
    assert favicons[0].valid is True
    assert isinstance(favicons[0].image, Image.Image) is True
    assert favicons[0].width == 500
    assert favicons[0].height == 200