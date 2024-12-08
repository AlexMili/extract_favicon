import base64
import io
import os
import re
from typing import NamedTuple, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse, urlunparse

import defusedxml.ElementTree as ETree
from bs4 import BeautifulSoup
from bs4.element import Tag
from PIL import Image, UnidentifiedImageError
from reachable import is_reachable


LINK_TAGS: list[str] = [
    "icon",
    "shortcut icon",
    "apple-touch-icon",
    "apple-touch-icon-precomposed",
    "mask-icon",
]

# Source:
# https://learn.microsoft.com/en-us/previous-versions/windows/internet-explorer/ie-developer/platform-apis/hh772707(v=vs.85)
META_TAGS: list[str] = [
    "msapplication-TileImage",
    "msapplication-square70x70logo",
    "msapplication-square150x150logo",
    "msapplication-wide310x150logo",
    "msapplication-square310x310logo",
]

# A fallback is a URL automatically checked by the browser
# without explicit declaration in the HTML.
# See
# https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html#//apple_ref/doc/uid/TP40002051-CH3-SW4
# https://developer.apple.com/design/human-interface-guidelines/app-icons#iOS-iPadOS-app-icon-sizes
FALLBACKS: list[str] = [
    "favicon.ico",
    "apple-touch-icon.png",
    "apple-touch-icon-180x180.png",
    "apple-touch-icon-167x167.png",
    "apple-touch-icon-152x152.png",
    "apple-touch-icon-120x120.png",
    "apple-touch-icon-114x114.png",
    "apple-touch-icon-80x80.png",
    "apple-touch-icon-87x87.png",
    "apple-touch-icon-76x76.png",
    "apple-touch-icon-58x58.png",
    "apple-touch-icon-precomposed.png",
]

SIZE_RE: re.Pattern[str] = re.compile(
    r"(?P<width>\d{2,4})x(?P<height>\d{2,4})", flags=re.IGNORECASE
)


class Favicon(NamedTuple):
    url: str
    format: Optional[str]
    width: int = 0
    height: int = 0


class FaviconURL(NamedTuple):
    url: str
    final_url: str
    redirected: bool
    status_code: int


class RealFavicon(NamedTuple):
    url: FaviconURL
    format: Optional[str]
    valid: bool
    original: Favicon
    image: Optional[Union[Image.Image, bytes]] = None
    width: int = 0
    height: int = 0


def _has_content(text: Optional[str]) -> bool:
    """Check if a string contains something.

    Args:
        text: the string to check.

    Returns:
        True if `text` is not None and its length is greater than 0.
    """
    if text is None or len(text) == 0:
        return False
    else:
        return True


# From https://github.com/scottwernervt/favicon/
def _is_absolute(url: str) -> bool:
    """Check if an URL is absolute.

    Args:
        url: website's URL.

    Returns:
        If full URL or relative path.
    """
    return _has_content(urlparse(url).netloc)


def _get_dimension(tag: Tag) -> Tuple[int, int]:
    """Get icon dimensions from size attribute or icon filename.

    Args:
        tag: Link or meta tag.

    Returns:
        If found, width and height, else (0,0).
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


def from_html(
    html: str, root_url: Optional[str] = None, include_fallbacks: bool = False
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

    tags: set[Tag] = set()
    for rel in LINK_TAGS:
        for link_tag in page.find_all(
            "link",
            attrs={"rel": lambda r: _has_content(r) and r.lower() == rel, "href": True},
        ):
            tags.add(link_tag)

    for tag in META_TAGS:
        for meta_tag in page.find_all(
            "meta",
            attrs={
                "name": lambda n: _has_content(n) and n.lower() == tag.lower(),
                "content": True,
            },
        ):
            tags.add(meta_tag)

    favicons = set()
    for tag in tags:
        href = tag.get("href") or tag.get("content") or ""  # type: ignore
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

            favicon = Favicon(href, suffix, 0, 0)
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

        width, height = _get_dimension(tag)
        _, ext = os.path.splitext(url_parsed.path)

        favicon = Favicon(url_parsed.geturl(), ext[1:].lower(), width, height)
        favicons.add(favicon)

    if include_fallbacks is True and len(favicons) == 0:
        for href in FALLBACKS:
            if root_url is not None:
                href = urljoin(root_url, href)

            _, ext = os.path.splitext(href)

            favicon = Favicon(href, ext[1:].lower())

    return favicons


def _get_root_url(url: str) -> str:
    parsed_url = urlparse(url)
    url_replaced = parsed_url._replace(query="", path="")
    return urlunparse(url_replaced)


def from_url(url: str, include_fallbacks: bool = False) -> set[Favicon]:
    result = is_reachable(url, head_optim=False, include_response=True)

    if result["success"] is True:
        favicons = from_html(
            result["response"].content,
            root_url=_get_root_url(result.get("final_url", None) or url),
            include_fallbacks=include_fallbacks,
        )
    else:
        favicons = set()

    return favicons


def _load_image(bytes_content: bytes) -> Tuple[Optional[Image.Image], bool]:
    is_valid: bool = False
    img: Optional[Image.Image] = None

    try:
        bytes_stream = io.BytesIO(bytes_content)
        img = Image.open(bytes_stream)
        img.verify()
        is_valid = True
        # Since verify() closes the file cursor, we open it again for further processing
        img = Image.open(bytes_stream)
    except UnidentifiedImageError:
        is_valid = False
    except OSError as e:  # noqa
        # Usually malformed images
        is_valid = False

    return img, is_valid


def download(favicons: list[Favicon]) -> list[RealFavicon]:
    real_favicons = []
    for fav in favicons:
        if fav.url[:5] != "data:":
            result = is_reachable(fav.url, head_optim=False, include_response=True)

            fav_url = FaviconURL(
                fav.url,
                final_url=result.get("final_url", fav.url),
                redirected="redirect" in result,
                status_code=result.get("status_code", -1),
            )

            if result["success"] is False:
                real_favicons.append(
                    RealFavicon(
                        fav_url,
                        None,
                        width=0,
                        height=0,
                        original=fav,
                        image=None,
                        valid=False,
                    )
                )
                continue

            filename = os.path.basename(urlparse(fav.url).path)
            if filename.lower().endswith(".svg") is True:
                root = ETree.fromstring(result["response"].content)

                # Check if the root tag is SVG
                if root.tag.lower().endswith("svg"):
                    is_valid = True
                else:
                    is_valid = False

                width = 0
                height = 0

                if "width" in root.attrib:
                    try:
                        width = int(root.attrib["width"])
                    except ValueError:
                        pass

                if "height" in root.attrib:
                    try:
                        height = int(root.attrib["height"])
                    except ValueError:
                        pass

                real_favicons.append(
                    RealFavicon(
                        fav_url,
                        "svg",
                        width=width,
                        height=height,
                        valid=is_valid,
                        image=ETree.tostring(root, encoding="utf-8"),
                        original=fav,
                    )
                )
            else:
                img, is_valid = _load_image(result["response"].content)

                width = height = 0
                img_format = None
                if img is not None:
                    width, height = img.size
                    img_format = img.format.lower()

                real_favicons.append(
                    RealFavicon(
                        fav_url,
                        img_format,
                        width=width,
                        height=height,
                        valid=is_valid,
                        image=img,
                        original=fav,
                    )
                )
        else:
            data_img = fav.url.split(",")
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
            img, is_valid = _load_image(bytes_content)

            fav_url = FaviconURL(
                fav.url, final_url=fav.url, redirected=False, status_code=200
            )

            width = height = 0
            img_format = None
            if img is not None:
                width, height = img.size
                img_format = img.format.lower()

            real_favicons.append(
                RealFavicon(
                    fav_url,
                    img_format,
                    width=width,
                    height=height,
                    valid=is_valid,
                    image=img,
                    original=fav,
                )
            )

    return real_favicons
