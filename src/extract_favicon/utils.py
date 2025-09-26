import re
from typing import Optional, Tuple, Union
from urllib.parse import urlparse, urlunparse

from bs4.element import AttributeValueList, Tag

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


def _get_tag_elt(tag: Tag, element: str) -> Union[str, None]:
    elt = tag.get(element)
    elt_str: Union[str, None] = None

    if isinstance(elt, AttributeValueList):
        elt_str = " ".join(elt)
    elif elt is not None:
        elt_str = elt

    return elt_str


def _get_dimension(tag: Tag) -> Tuple[int, int]:
    """Get icon dimensions from size attribute or icon filename.

    Args:
        tag: Link or meta tag.

    Returns:
        If found, width and height, else (0,0).
    """
    sizes = _get_tag_elt(tag, "sizes")

    if sizes and sizes.lower() != "any":
        # "16x16 32x32 64x64"
        choices = sizes.split(" ")
        choices.sort(reverse=True)
        width, height = re.split(r"[x\xd7]", choices[0], flags=re.I)
    else:
        filename = _get_tag_elt(tag, "href") or _get_tag_elt(tag, "content") or ""

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


def _largest_ico_from_header(data: bytes) -> Optional[Tuple[int, int]]:
    """
    Return (width, height) of the largest embedded image in an ICO file by
    inspecting only the file header (ICONDIR) and its directory entries
    (ICONDIRENTRY). This avoids fully decoding any image data.

    ICO structure (little-endian):
      ICONDIR (6 bytes total)
        0-1: reserved = 0
        2-3: type     = 1 for ICO (2 for CUR)
        4-5: count    = number of images (N)

      ICONDIRENTRY (16 bytes) repeated N times:
        +0 : width        (BYTE; 0 means 256)
        +1 : height       (BYTE; 0 means 256)
        +2 : colorCount   (BYTE; 0 if >= 256 colors)  [unused here]
        +3 : reserved     (BYTE; must be 0)           [unused here]
        +4 : planes       (WORD)                      [unused here]
        +6 : bitCount     (WORD)  — image bit depth, used as tie-breaker
        +8 : bytesInRes   (DWORD) — size of the image data, tie-breaker
        +12: imageOffset  (DWORD) — offset to the image data  [unused here]

    Selection policy:
      - Prefer the largest area (width * height).
      - If areas tie, prefer greater bit depth (bitCount).
      - If still tied, prefer larger resource size (bytesInRes).
      - If still tied, prefer the wider image (arbitrary but stable).
    """
    # Need at least the 6-byte ICONDIR to read reserved/type/count.
    if len(data) < 6:
        return None

    # Read ICONDIR -----------------------------------------------
    reserved = int.from_bytes(data[0:2], "little")
    # type 1 = ICO, 2 = CUR (cursor). We only handle ICO here.
    typ = int.from_bytes(data[2:4], "little")
    # Number of directory entries (images) following ICONDIR.
    count = int.from_bytes(data[4:6], "little")

    # Basic validation: bail if not an ICO, or no images.
    if reserved != 0 or typ != 1 or count == 0:
        return None

    # Total bytes needed to cover the full directory table:
    # 6 bytes (ICONDIR) + 16 bytes per ICONDIRENTRY.
    table_len = 6 + 16 * count
    # If we don't yet have the full table, the caller should feed more bytes.
    if len(data) < table_len:
        return None

    # Track the "best" candidate using a sortable key.
    # best_key is a tuple reflecting our selection policy:
    #   (area, bitCount, bytesInRes, width)
    # Start with an intentionally tiny baseline so the first real entry wins.
    best_key = (-1, -1, -1, -1)
    best = (0, 0)  # (width, height) to return
    off = 6  # Byte offset where the first ICONDIRENTRY begins

    # Iterate over all N directory entries.
    for i in range(count):
        # Width/height are stored as single bytes where 0 encodes 256.
        # This is a quirk of the ICO format to represent 256 in one byte.
        w = data[off] or 256
        h = data[off + 1] or 256

        # We don't use planes here; bitCount is a proxy for quality/depth.
        bitCount = int.from_bytes(data[off + 6 : off + 8], "little")
        # bytesInRes approximates how detailed the resource is at the same size
        # (e.g., PNG vs BMP, more metadata, etc.). Use as a tie-breaker.
        bytesInRes = int.from_bytes(data[off + 8 : off + 12], "little")

        # Build comparison key according to our policy.
        key = (w * h, bitCount, bytesInRes, w)

        # Keep the entry with the lexicographically greatest key.
        if key > best_key:
            best_key = key
            best = (w, h)

        # Advance to the next ICONDIRENTRY (fixed 16-byte stride).
        off += 16

    return best
