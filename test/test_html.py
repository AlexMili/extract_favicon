import pytest

import extract_favicon


HTML: str = """
<!DOCTYPE html>
<html lang="en">
    <head>%content%</head>
    <body></body>
</html>
"""


@pytest.mark.parametrize(
    "tag",
    [
        '<link rel="icon" href="favicon.ico">',
        '<link rel="ICON" href="favicon.ico">',
        '<link rel="shortcut icon" href="favicon.ico">',
        '<link rel="apple-touch-icon" href="favicon.ico">',
        '<link rel="apple-touch-icon-precomposed" href="favicon.ico">',
    ],
    ids=[
        "icon",
        "ICON",
        "shortcut icon",
        "apple-touch-icon",
        "apple-touch-icon-precomposed",
    ],
)
def test_link_tag(tag: str):
    favicons = extract_favicon.from_html(HTML.replace("%content%", tag))
    assert len(favicons) == 1


@pytest.mark.parametrize(
    "tag,size",
    [
        ('<link rel="icon" href="logo.png" sizes="any">', (0, 0)),
        ('<link rel="icon" href="logo.png" sizes="16x16">', (16, 16)),
        ('<link rel="icon" href="logo.png" sizes="24x24+">', (24, 24)),
        ('<link rel="icon" href="logo.png" sizes="32x32 64x64">', (64, 64)),
        ('<link rel="icon" href="logo.png" sizes="64x64 32x32">', (64, 64)),
        ('<link rel="icon" href="logo-128x128.png" sizes="any">', (128, 128)),
        ('<link rel="icon" href="logo.png" sizes="16×16">', (16, 16)),
        (
            '<link data-react-helmet="true" href="/public/favicons/color-1.ico" rel="shortcut icon" sizes="192X192" type="image/x-icon"/>',
            (192, 192),
        ),
    ],
    ids=[
        "any",
        "16x16",
        "24x24+",
        "32x32 64x64",
        "64x64 32x32",
        "logo-128x128.png",
        "new york times",
        "Uppercase X",
    ],
)
def test_link_tag_sizes_attribute(tag, size):
    favicons = extract_favicon.from_html(HTML.replace("%content%", tag))
    assert len(favicons) == 1
    icon = favicons.pop()
    assert icon.width == size[0] and icon.height == size[1]


@pytest.mark.parametrize(
    "tag,url",
    [
        ('<link rel="icon" href="logo.png">', "https://example.com/logo.png"),
        ('<link rel="icon" href="logo.png\t">', "https://example.com/logo.png"),
        (
            '<link rel="icon" href="/static/logo.png">',
            "https://example.com/static/logo.png",
        ),
        (
            '<link rel="icon" href="https://example.com/logo.png">',
            "https://example.com/logo.png",
        ),
        (
            '<link rel="icon" href="//example.com/logo.png">',
            "https://example.com/logo.png",
        ),
        (
            '<link rel="icon" href="https://example.com/logo.png?v2">',
            "https://example.com/logo.png?v2",
        ),
    ],
    ids=[
        "filename",
        "filename \\t",
        "relative",
        "https",
        "forward slashes",
        "query string",
    ],
)
def test_link_tag_href_attribute(tag, url):
    favicons = extract_favicon.from_html(HTML.replace("%content%", tag), root_url=url)
    assert len(favicons) == 1
    assert favicons.pop().url == url


@pytest.mark.parametrize(
    "tag",
    [
        '<link rel="icon" type="image/jpeg" sizes="x" href="/favicon.jpg" />',
    ],
    ids=[
        "Malformed icon size",
    ],
)
def test_malformed_link(tag):
    favicons = extract_favicon.from_html(HTML.replace("%content%", tag))
    assert len(favicons) == 1


@pytest.mark.parametrize(
    "tag",
    [
        '<link rel="icon" href="">',
        '<link rel="icon">',
    ],
    ids=[
        "Href str length 0",
        "No href",
    ],
)
def test_link_tag_empty_href_attribute(tag):
    favicons = extract_favicon.from_html(HTML.replace("%content%", tag))
    assert len(favicons) == 0


@pytest.mark.parametrize(
    "tag",
    [
        '<meta name="msapplication-TileImage" content="favicon.ico">',
        '<meta name="msapplication-tileimage" content="favicon.ico">',
    ],
    ids=["msapplication-TileImage", "msapplication-tileimage"],
)
def test_meta_tag(tag):
    favicons = extract_favicon.from_html(HTML.replace("%content%", tag))
    assert len(favicons) == 1


@pytest.mark.parametrize(
    "tag",
    [
        '<meta content="en-US" data-rh="true" itemprop="inLanguage"/>',
        '<meta name="msapplication-tileimage" content="">',
        '<meta name="msapplication-tileimage">',
    ],
    ids=["Missing meta", "Empty meta str length 0", "Empty meta content"],
)
def test_invalid_meta_tag(tag):
    favicons = extract_favicon.from_html(HTML.replace("%content%", tag))
    assert len(favicons) == 0


@pytest.mark.parametrize(
    "tag",
    [
        '<link rel="icon" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg==">',
    ],
    ids=["Base64 image"],
)
def test_base64(tag):
    favicons = extract_favicon.from_html(HTML.replace("%content%", tag))
    assert len(favicons) == 1
    favicon = favicons.pop()
    assert favicon.format == "png"
    assert favicon.width == 0
    assert favicon.height == 0


# Test to verify <base> tag handling
@pytest.mark.parametrize(
    "tag",
    [
        '<base href="http://example.com/">\n<link rel="icon" type="image/jpeg" href="/favicon.jpg" />',
    ],
    ids=[
        "Base tag with relative icon",
    ],
)
def test_base_tag_link(tag):
    favicons = extract_favicon.from_html(HTML.replace("%content%", tag))
    assert len(favicons) == 1
    favicon = favicons.pop()
    assert favicon.url == "http://example.com/favicon.jpg"
