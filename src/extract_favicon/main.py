import base64
import io
import os
import re
from typing import NamedTuple, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag
from PIL import Image


LINK_TAGS: list[str] = [
    "icon",
    "shortcut icon",
    "apple-touch-icon",
    "apple-touch-icon-precomposed",
]


SIZE_RE: re.Pattern[str] = re.compile(
    r"(?P<width>\d{2,4})x(?P<height>\d{2,4})", flags=re.IGNORECASE
)


class Favicon(NamedTuple):
    url: str
    format: str
    width: int = 0
    height: int = 0


def _has_content(text: Optional[str]) -> bool:
    if text is None or len(text) == 0:
        return False
    else:
        return True


# From https://github.com/scottwernervt/favicon/
def _is_absolute(url: str) -> bool:
    """Check if an URL is absolute.

    :param url: URL for site.
    :type url: str

    :return: True if homepage and false if it has a path.
    :rtype: bool
    """
    return _has_content(urlparse(url).netloc)


def from_html(
    html: str, root_url: Optional[str] = None, include_default_favicon: bool = False
) -> set[Favicon]:
    """Extract all favicons in a given HTML.

    Args:
        html: HTML to parse.
        root_url: Root URL where the favicon is located.
        include_default_favicon: Include /favicon.ico in the list when no other
            favicons have been found

    Returns:
        A set of favicons.
    """
    page = BeautifulSoup(html, features="html.parser")

    # Handle the <base> tag if it exists
    # We priorize user's value for root_url over base tag
    base_tag = page.find("base", href=True)
    if base_tag is not None and root_url is None:
        root_url = base_tag["href"]

    tags = set()
    for rel in LINK_TAGS:
        for link_tag in page.find_all(
            "link",
            attrs={"rel": lambda r: _has_content(r) and r.lower() == rel, "href": True},
        ):
            tags.add(link_tag)

    meta_name = "msapplication-TileImage"
    for meta_tag in page.find_all(
        "meta",
        attrs={
            "name": lambda n: _has_content(n) and n.lower() == meta_name.lower(),
            "content": True,
        },
    ):
        tags.add(meta_tag)

    favicons = set()
    for tag in tags:
        href = tag.get("href") or tag.get("content") or ""
        href = href.strip()

        # We skip if there is not content in href
        if len(href) == 0:
            continue

        if href[:5] == "data:":
            # This is a inline base64 image
            data_img = href.split(",")
            suffix = (
                data_img[0]
                .replace("data:", "")
                .replace(";base64", "")
                .replace("image", "")
                .replace("/", "")
                .lower()
            )

            if suffix == "svg+xml":
                suffix = "svg"

            bytes_content = base64.b64decode(data_img[1])
            bytes_stream = io.BytesIO(bytes_content)
            img = Image.open(bytes_stream)
            width, height = img.size

            favicon = Favicon(href, suffix, width, height)
            favicons.add(favicon)
            continue
        elif root_url is not None:
            if _is_absolute(href) is True:
                url_parsed = href
            else:
                url_parsed = urljoin(root_url, href)

            # Repair '//cdn.network.com/favicon.png' or `icon.png?v2`
            scheme = urlparse(root_url).scheme
            url_parsed = urlparse(url_parsed, scheme=scheme)
        else:
            url_parsed = urlparse(href)

        width, height = get_dimension(tag)
        _, ext = os.path.splitext(url_parsed.path)

        favicon = Favicon(url_parsed.geturl(), ext[1:].lower(), width, height)
        favicons.add(favicon)

    if include_default_favicon is True and len(favicons) == 0:
        href = "/favicon.ico"
        if root_url is not None:
            url_parsed = urljoin(root_url, href)
        else:
            url_parsed = urlparse(href)

        _, ext = os.path.splitext(url_parsed.path)

        favicon = Favicon(url_parsed.geturl(), ext[1:].lower())

    return favicons


def get_dimension(tag: Tag) -> Tuple[int, int]:
    """Get icon dimensions from size attribute or icon filename.

    :param tag: Link or meta tag.
    :type tag: :class:`bs4.element.Tag`

    :return: If found, width and height, else (0,0).
    :rtype: tuple(int, int)
    """
    sizes = tag.get("sizes", "")
    if sizes and sizes != "any":
        # "16x16 32x32 64x64"
        size = sizes.split(" ")
        size.sort(reverse=True)
        width, height = re.split(r"[x\xd7]", size[0], flags=re.I)
    else:
        filename = tag.get("href") or tag.get("content") or ""
        size = SIZE_RE.search(filename)
        if size:
            width, height = size.group("width"), size.group("height")
        else:
            width, height = "0", "0"

    # Repair bad html attribute values: sizes="192x192+"
    width = "".join(c for c in width if c.isdigit())
    height = "".join(c for c in height if c.isdigit())

    width = int(width) if _has_content(width) else 0
    height = int(height) if _has_content(height) else 0

    return width, height
