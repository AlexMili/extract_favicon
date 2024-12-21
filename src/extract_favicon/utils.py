import re
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

from bs4.element import Tag

from .config import SIZE_RE, Favicon


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


def _get_root_url(url: str) -> str:
    """
    Extracts the root URL from a given URL, removing any path, query, or fragments.

    This function takes a full URL and parses it to isolate the root components:
    scheme (e.g., "http"), netloc (e.g., "example.com"), and optional port. It
    then returns the reconstructed URL without any path, query parameters, or
    fragments.

    Args:
        url: The URL from which to extract the root.

    Returns:
        The root URL, including the scheme and netloc, but without any
            additional paths, queries, or fragments.
    """
    parsed_url = urlparse(url)
    url_replaced = parsed_url._replace(query="", path="")
    return urlunparse(url_replaced)


def _get_url(fav: Favicon) -> str:
    if fav.http is not None:
        return fav.http.final_url
    else:
        return fav.url
