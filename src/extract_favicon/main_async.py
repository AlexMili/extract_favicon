import asyncio
from typing import Optional, Union

import httpx
import tldextract
from PIL import ImageFile
from reachable import is_reachable_async
from reachable.client import AsyncClient

from extract_favicon.main import from_html, generate_favicon

from .config import STRATEGIES, Favicon, FaviconHttp
from .loader import _load_base64_img, load_image_async
from .utils import _get_root_url


async def from_url(
    url: str, include_fallbacks: bool = False, client: Optional[AsyncClient] = None
) -> set[Favicon]:
    result = await is_reachable_async(
        url, head_optim=False, include_response=True, client=client
    )

    if result["success"] is True:
        favicons = from_html(
            result["response"].content,
            root_url=_get_root_url(result.get("final_url", None) or url),
            include_fallbacks=include_fallbacks,
        )
    else:
        favicons = set()

    return favicons


async def from_duckduckgo(url: str, client: Optional[AsyncClient] = None) -> Favicon:
    tld = tldextract.extract(url)
    duckduckgo_url = f"https://icons.duckduckgo.com/ip3/{tld.fqdn}.ico"

    favicon = Favicon(duckduckgo_url)
    favicon = await load_image_async(favicon, client=client)

    return favicon


async def from_google(
    url: str, client: Optional[AsyncClient] = None, size: int = 256
) -> Favicon:
    tld = tldextract.extract(url)
    google_url = f"https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{tld.fqdn}&size={size}"

    favicon = Favicon(google_url)
    favicon = await load_image_async(favicon, client=client)

    return favicon


async def download(
    favicons: Union[list[Favicon], set[Favicon]],
    mode: str = "all",
    include_unknown: bool = True,
    sleep_time: int = 2,
    sort: str = "ASC",
    client: Optional[AsyncClient] = None,
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
        fav = await load_image_async(fav, client=client)

        if fav.reachable is True and fav.valid is True:
            real_favicons.append(fav)

        # If we are in these modes, we need to exit the for loop
        if mode in ["largest", "smallest"]:
            break

        # Wait before next request to avoid detection but skip it for the last item
        if idx < len_process - 1:
            await asyncio.sleep(sleep_time)

    real_favicons = sorted(
        real_favicons, key=lambda x: x.width * x.height, reverse=sort.lower() == "desc"
    )

    return real_favicons


async def guess_size(
    favicon: Favicon,
    chunk_size: int = 512,
    force: bool = False,
    client: Optional[AsyncClient] = None,
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
        client = AsyncClient()
        await client.open()
    else:
        close_client = False

    try:
        async with client.stream("GET", favicon.url) as response:
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

                async for chunk in response.aiter_bytes(chunk_size=chunk_size):
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
        await client.close()

    return favicon


async def guess_missing_sizes(
    favicons: Union[list[Favicon], set[Favicon]],
    chunk_size: int = 512,
    sleep_time: int = 1,
    load_base64_img: bool = False,
    client: Optional[AsyncClient] = None,
) -> list[Favicon]:
    favs = list(favicons)

    len_favs = len(favs)
    for idx in range(len_favs):
        if favs[idx].url[:5] == "data:" and load_base64_img is True:
            favs[idx] = _load_base64_img(favs[idx])
        else:
            favs[idx] = await guess_size(
                favs[idx], chunk_size=chunk_size, client=client
            )

            # Skip sleep when last iteration
            if idx < len_favs - 1:
                await asyncio.sleep(sleep_time)

    return favs


async def check_availability(
    favicons: Union[list[Favicon], set[Favicon]],
    sleep_time: int = 1,
    force: bool = False,
    client: Optional[AsyncClient] = None,
) -> list[Favicon]:
    favs = list(favicons)

    len_favs = len(favs)
    for idx in range(len(favs)):
        # If the favicon is already reachable, we save a request and skip it
        if favs[idx].reachable is True and force is False:
            continue
        elif favs[idx].url[:5] == "data:":
            favs[idx] = favs[idx]._replace(reachable=True)
            continue

        result = await is_reachable_async(favs[idx].url, head_optim=True, client=client)

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
            await asyncio.sleep(sleep_time)

    return favs


async def get_best_favicon(
    url: str,
    html: Optional[Union[str, bytes]] = None,
    client: Optional[AsyncClient] = None,
    strategy: list[str] = ["content", "duckduckgo", "google", "generate"],
    include_fallbacks: bool = True,
) -> Optional[Favicon]:
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
                favicons = await from_url(
                    url, include_fallbacks=include_fallbacks, client=client
                )

            favicons_data = await guess_missing_sizes(favicons, load_base64_img=True)
            favicons_data = await check_availability(favicons_data, client=client)

            favicons_data = await download(favicons_data, mode="largest", client=client)

            if len(favicons_data) > 0:
                favicon = favicons_data[0]

        elif strat.lower() == "duckduckgo":
            fav = await from_duckduckgo(url, client)

            if (
                fav.reachable is True
                and fav.valid is True
                and fav.width > 0
                and fav.height > 0
            ):
                favicon = fav

        elif strat.lower() == "google":
            fav = await from_google(url, client)

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
