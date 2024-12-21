import re
from typing import NamedTuple, Optional, Union

from PIL import Image


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

STRATEGIES: list[str] = ["content", "duckduckgo", "google", "generate"]


class FaviconHttp(NamedTuple):
    original_url: str
    final_url: str
    redirected: bool
    status_code: int


class Favicon(NamedTuple):
    url: str
    width: int = 0
    height: int = 0
    format: Optional[str] = None
    valid: Optional[bool] = None
    reachable: Optional[bool] = None
    image: Optional[Union[Image.Image, bytes]] = None
    http: Optional[FaviconHttp] = None
