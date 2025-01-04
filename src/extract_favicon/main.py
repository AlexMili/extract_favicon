import os
import time
from typing import Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
import tldextract
from bs4 import BeautifulSoup
from bs4.element import Tag
from PIL import ImageFile
from reachable import is_reachable
from reachable.client import Client

from .config import FALLBACKS, LINK_TAGS, META_TAGS, STRATEGIES, Favicon, FaviconHttp
from .loader import _load_base64_img, _load_svg_img, load_image
from .utils import _get_dimension, _get_root_url, _has_content, _is_absolute


def from_html(
    html: str,
    root_url: Optional[str] = None,
    include_fallbacks: bool = False,
) -> set[Favicon]:
    """Extract all favicons in a given HTML.

    Args:
        html: HTML to parse.
        root_url: Root URL where the favicon is located.
        include_fallbacks: Whether to include fallback favicons like `/favicon.ico`.

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

            favicon = Favicon(href, format=suffix, width=0, height=0)
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

        favicon = Favicon(
            url_parsed.geturl(), format=ext[1:].lower(), width=width, height=height
        )
        favicons.add(favicon)

    if include_fallbacks is True and len(favicons) == 0:
        for href in FALLBACKS:
            if root_url is not None:
                href = urljoin(root_url, href)

            _, ext = os.path.splitext(href)

            favicons.add(Favicon(href, format=ext[1:].lower()))

    return favicons


def from_url(
    url: str, include_fallbacks: bool = False, client: Optional[Client] = None
) -> set[Favicon]:
    """Extracts favicons from a given URL.

    This function attempts to retrieve the specified URL, parse its HTML, and extract any
    associated favicons. If the URL is reachable and returns a successful response, the
    function will parse the content for favicon references. If `include_fallbacks` is True,
    it will also attempt to find fallback icons (e.g., by checking default icon paths).
    If the URL is not reachable or returns an error response, an empty set is returned.

    Args:
        url: The URL from which to extract favicons.
        include_fallbacks: Whether to include fallback favicons if none are
            explicitly defined. Defaults to False.
        client: A custom client instance from `reachable` package to use for performing
            the HTTP request. If None, a default client configuration is used.

    Returns:
        A set of `Favicon` objects found in the target URL's HTML.

    """
    result = is_reachable(url, head_optim=False, include_response=True, client=client)

    if result["success"] is True:
        favicons = from_html(
            result["response"].content,
            root_url=_get_root_url(result.get("final_url", None) or url),
            include_fallbacks=include_fallbacks,
        )
    else:
        favicons = set()

    return favicons


def from_duckduckgo(url: str, client: Optional[Client] = None) -> Favicon:
    """
    Retrieves a website's favicon via DuckDuckGo's Favicon public API.

    This function uses `tldextract` to parse the given URL and constructs a DuckDuckGo
    favicon URL using the top-level domain. It then fetch and populate a `Favicon`
    object with any available metadata (e.g., width, height and reachability).

    Args:
        url: The target website URL.
        client: A custom HTTP client to use for the request

    Returns:
        A `Favicon` object containing favicon data.
    """
    tld = tldextract.extract(url)
    duckduckgo_url = f"https://icons.duckduckgo.com/ip3/{tld.fqdn}.ico"

    favicon = Favicon(duckduckgo_url)
    favicon = load_image(favicon, client=client)

    return favicon


def from_google(url: str, client: Optional[Client] = None, size: int = 256) -> Favicon:
    """
    Retrieves a website's favicon via Google's Favicon public API.

    This function uses `tldextract` to parse the given URL and constructs a Google
    favicon URL using the top-level domain. It then fetch and populate a `Favicon`
    object with any available metadata (e.g., width, height and reachability).

    Args:
        url: The target website URL.
        client: A custom HTTP client to use for the request

    Returns:
        A `Favicon` object containing favicon data.
    """
    tld = tldextract.extract(url)
    google_url = f"https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{tld.fqdn}&size={size}"

    favicon = Favicon(google_url)
    favicon = load_image(favicon, client=client)

    return favicon


def download(
    favicons: Union[list[Favicon], set[Favicon]],
    mode: str = "all",
    include_unknown: bool = True,
    sleep_time: int = 2,
    sort: str = "ASC",
    client: Optional[Client] = None,
) -> list[Favicon]:
    """Download previsouly extracted favicons.

    Args:
        favicons: list of favicons to download.
        mode: select the strategy to download favicons.
            - `all`: download all favicons in the list.
            - `largest`: only download the largest favicon in the list.
            - `smallest`: only download the smallest favicon in the list.
        include_unknown: include or not images with no width/height information.
        sleep_time: number of seconds to wait between each requests to avoid blocking.
        sort: sort favicons by size in ASC or DESC order. Only used for mode `all`.
        client: A custom client instance from `reachable` package to use for performing
            the HTTP request. If None, a default client configuration is used.

    Returns:
        A list of favicons.
    """
    real_favicons: list[Favicon] = []
    to_process: list[Favicon] = []

    if include_unknown is False:
        favicons = list(filter(lambda x: x.width != 0 and x.height != 0, favicons))

    if mode.lower() in ["largest", "smallest"]:
        to_process = sorted(
            favicons, key=lambda x: x.width * x.height, reverse=mode == "largest"
        )
    else:
        to_process = list(favicons)

    len_process = len(to_process)
    for idx, fav in enumerate(to_process):
        fav = load_image(fav, client=client)

        if fav.reachable is True and fav.valid is True:
            real_favicons.append(fav)

        # If we are in one of these modes, we need to exit the for loop
        if mode in ["largest", "smallest"]:
            break

        # Wait before next request to avoid detection but skip it for the last item
        if idx < len_process - 1:
            time.sleep(sleep_time)

    real_favicons = sorted(
        real_favicons, key=lambda x: x.width * x.height, reverse=sort.lower() == "desc"
    )

    return real_favicons


def guess_size(
    favicon: Favicon,
    chunk_size: int = 512,
    force: bool = False,
    client: Optional[Client] = None,
) -> Favicon:
    """Get size of image by requesting first bytes.

    Args:
        favicon: the favicon object from which to guess the size.
        chunk_size: bytes size to iterate over image stream.
        force: try to guess the size even if the width and height are not zero.

    Returns:
        The Favicon object with updated width, height, reachable and http parameters.
    """
    if favicon.width != 0 and favicon.height != 0 and force is False:
        # TODO: add warning log
        return favicon
    elif favicon.reachable is False and force is False:
        # TODO: add warning log
        return favicon

    close_client: bool = True
    if client is None:
        client = Client()
    else:
        close_client = False

    try:
        with client.stream("GET", favicon.url) as response:
            fav_http = FaviconHttp(
                original_url=favicon.url,
                final_url=str(response.url),
                redirected=favicon.url != str(response.url),
                status_code=response.status_code,
            )

            if (
                200 <= response.status_code < 300
                and "content-type" in response.headers
                and "image" in response.headers["content-type"]
            ):
                favicon = favicon._replace(reachable=True, http=fav_http)

                bytes_parsed: int = 0
                max_bytes_parsed: int = 2048
                chunk_size = 512
                parser = ImageFile.Parser()

                for chunk in response.iter_bytes(chunk_size=chunk_size):
                    bytes_parsed += chunk_size
                    # partial_data += chunk

                    parser.feed(chunk)

                    if parser.image is not None or bytes_parsed > max_bytes_parsed:
                        img = parser.image
                        if img is not None:
                            width, height = img.size
                            favicon = favicon._replace(width=width, height=height)
                        break
            elif 200 <= response.status_code < 300:
                # No "image" content-type so we put valid=False
                favicon = favicon._replace(reachable=True, valid=False, http=fav_http)
            else:
                favicon = favicon._replace(reachable=False, valid=False, http=fav_http)
    except (
        httpx.ConnectError,
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.RemoteProtocolError,
        httpx.ReadError,
    ):
        fav_http = FaviconHttp(
            original_url=favicon.url,
            final_url=favicon.url,
            redirected=False,
            status_code=-1,
        )
        favicon = favicon._replace(reachable=False, valid=False, http=fav_http)

    if close_client is True:
        client.close()

    return favicon


def guess_missing_sizes(
    favicons: Union[list[Favicon], set[Favicon]],
    chunk_size: int = 512,
    sleep_time: int = 1,
    load_base64_img: bool = False,
    client: Optional[Client] = None,
) -> list[Favicon]:
    """
    Attempts to determine missing dimensions (width and height) of favicons.

    For each favicon in the provided collection, if the favicon is a base64-encoded
    image (data URL) and `load_base64_img` is True, the function decodes and loads
    the image to guess its dimensions. For non-base64 favicons with missing or zero
    dimensions, the function attempts to guess the size by partially downloading the
    icon data (using `guess_size`).

    Args:
        favicons: A list or set of `Favicon` objects for which to guess missing dimensions.
        chunk_size: The size of the data chunk to download for guessing dimensions of
            non-base64 images. Defaults to 512.
        sleep_time: The number of seconds to sleep between guessing attempts to avoid
            rate limits or overloading the server. Defaults to 1.
        load_base64_img: Whether to decode and load base64-encoded images (data URLs)
            to determine their dimensions. Defaults to False.

    Returns:
        A list of `Favicon` objects with dimensions updated where they could be determined.
    """
    favs = list(favicons)

    len_favs = len(favs)
    for idx in range(len_favs):
        if favs[idx].url[:5] == "data:" and load_base64_img is True:
            favs[idx] = _load_base64_img(favs[idx])
        else:
            favs[idx] = guess_size(favs[idx], chunk_size=chunk_size, client=client)

            # Skip sleep when last iteration
            if idx < len_favs - 1:
                time.sleep(sleep_time)

    return favs


def check_availability(
    favicons: Union[list[Favicon], set[Favicon]],
    sleep_time: int = 1,
    force: bool = False,
    client: Optional[Client] = None,
) -> list[Favicon]:
    """
    Checks the availability and final URLs of a collection of favicons.

    For each favicon in the provided list or set, this function sends a head request
    (or an optimized request if available) to check whether the favicon's URL is
    reachable. If the favicon is reachable, its `reachable` attribute is updated to
    True. If the request results in a redirect, the favicon's URL is updated to the
    final URL.

    A delay (`sleep_time`) can be specified between checks to avoid rate limits
    or overloading the server.

    Args:
        favicons: A collection of `Favicon` objects to check for availability.
        sleep_time: Number of seconds to sleep between each availability check to
            control request rate. Defaults to 1.
        force: Check again the availability even if it has already been checked.
        client: A custom client instance from `reachable` package to use for performing
            the HTTP request. If None, a default client configuration is used.

    Returns:
        A list of `Favicon` objects with updated `reachable` statuses and potentially
            updated URLs if redirects were encountered.
    """
    favs = list(favicons)

    len_favs = len(favs)
    for idx in range(len(favs)):
        # If the favicon is already reachable, we save a request and skip it
        if favs[idx].reachable is True and force is False:
            continue
        elif favs[idx].url[:5] == "data:":
            favs[idx] = favs[idx]._replace(reachable=True)
            continue

        result = is_reachable(favs[idx].url, head_optim=True, client=client)

        fav_http = FaviconHttp(
            original_url=favs[idx].url,
            final_url=result.get("final_url", favs[idx].url),
            redirected="redirect" in result,
            status_code=result.get("status_code", -1),
        )

        if result["success"] is True:
            favs[idx] = favs[idx]._replace(reachable=True, http=fav_http)
        else:
            favs[idx] = favs[idx]._replace(reachable=False, http=fav_http)

        # If has been redirected
        if "redirect" in result:
            favs[idx] = favs[idx]._replace(url=result.get("final_url", favs[idx].url))

        # Wait before next request to avoid detection but skip it for the last item
        if idx < len_favs - 1:
            time.sleep(sleep_time)

    return favs


def generate_favicon(url: str) -> Favicon:
    """
    Generates a placeholder favicon as an SVG containing the first letter of the domain.

    This function extracts the domain name from the provided URL using `tldextract`,
    takes the first letter of the domain (capitalized), and embeds it into an SVG
    image. The generated SVG is then loaded into a `Favicon` object.

    Args:
        url: The URL from which to extract the domain and generate the favicon.

    Returns:
        A `Favicon` instance populated with the generated SVG data.
    """
    tld = tldextract.extract(url)
    letter = tld.domain[0].upper()
    svg_data = f"""
    <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ccc"/>
        <text x="50%" y="60%" font-size="100px" text-anchor="middle" dominant-baseline="middle" fill="#000">{letter}</text>
    </svg>
    """

    favicon = Favicon(url)
    favicon = _load_svg_img(favicon, svg_data)

    return favicon


def get_best_favicon(
    url: str,
    html: Optional[Union[str, bytes]] = None,
    client: Optional[Client] = None,
    strategy: list[str] = ["content", "duckduckgo", "google", "generate"],
    include_fallbacks: bool = True,
) -> Optional[Favicon]:
    """
    Attempts to retrieve the best favicon for a given URL using multiple strategies.

    The function iterates over the specified strategies in order, stopping as soon as a valid
    favicon is found:
        - "content": Parses the provided HTML (if any) or fetches page content from the URL to
        extract favicons. It then guesses missing sizes, checks availability, and downloads
        the largest icon.
        - "duckduckgo": Retrieves a favicon from DuckDuckGo if the previous step fails.
        - "google": Retrieves a favicon from Google if the previous step fails.
        - "generate": Generates a placeholder favicon if all else fails.

    Args:
        url: The URL for which the favicon is being retrieved.
        html: Optional HTML content to parse. If not provided, the page content is retrieved
            from the URL.
        client: Optional HTTP client to use for network requests.
        strategy: A list of strategy names to attempt in sequence. Defaults to
            ["content", "duckduckgo", "google", "generate"].
        include_fallbacks: check for fallbacks URL for `content` strategy.

    Returns:
        The best found favicon if successful, otherwise None.

    Raises:
        ValueError: If an unrecognized strategy name is encountered in the list.
    """
    favicon = None

    for strat in strategy:
        if strat.lower() not in STRATEGIES:
            raise ValueError(f"{strat} strategy not recognized. Aborting.")

        if strat.lower() == "content":
            favicons = set()

            if html is not None and len(html) > 0:
                favicons = from_html(
                    str(html),
                    root_url=_get_root_url(url),
                    include_fallbacks=include_fallbacks,
                )
            else:
                favicons = from_url(
                    url, include_fallbacks=include_fallbacks, client=client
                )

            favicons_data = guess_missing_sizes(favicons, load_base64_img=True)
            favicons_data = check_availability(favicons_data, client=client)

            favicons_data = download(favicons_data, mode="largest", client=client)

            if len(favicons_data) > 0:
                favicon = favicons_data[0]

        elif strat.lower() == "duckduckgo":
            fav = from_duckduckgo(url, client)

            if (
                fav.reachable is True
                and fav.valid is True
                and fav.width > 0
                and fav.height > 0
            ):
                favicon = fav

        elif strat.lower() == "google":
            fav = from_google(url, client)

            if (
                fav.reachable is True
                and fav.valid is True
                and fav.width > 0
                and fav.height > 0
            ):
                favicon = fav

        elif strat.lower() == "generate":
            favicon = generate_favicon(url)

        if favicon is not None:
            break

    return favicon
