import base64
import os
import time
from typing import Optional, Tuple, Union
from urllib.parse import urlparse

import defusedxml.ElementTree as ETree
import httpx
from PIL import ImageFile
from reachable import is_reachable_async
from reachable.client import AsyncClient

from extract_favicon.main import (
    Favicon,
    FaviconURL,
    RealFavicon,
    _get_root_url,
    _load_image,
    from_html,
)


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


async def download(
    favicons: Union[list[Favicon], set[Favicon]],
    mode: str = "all",
    include_unknown: bool = True,
    sleep_time: int = 2,
    sort: str = "ASC",
    client: Optional[AsyncClient] = None,
) -> list[RealFavicon]:
    """Download previsouly extracted favicons.

    Args:
        favicons: list of favicons to download.
        mode: select the strategy to download favicons.
            - `all`: download all favicons in the list.
            - `biggest`: only download the biggest favicon in the list.
            - `smallest`: only download the smallest favicon in the list.
        include_unknown: include or not images with no width/height information.
        sleep_time: number of seconds to wait between each requests to avoid blocking.
        sort: sort favicons by size in ASC or DESC order. Only used for mode `all`.
        client: use common client to reduce HTTP overhead.

    Returns:
        A set of favicons.
    """
    real_favicons: list[RealFavicon] = []
    to_process: list[Favicon] = []

    if include_unknown is False:
        favicons = list(filter(lambda x: x.width != 0 and x.height != 0, favicons))

    if mode.lower() in ["biggest", "smallest"]:
        to_process = sorted(
            favicons, key=lambda x: x.width * x.height, reverse=mode == "biggest"
        )
    else:
        to_process = list(favicons)

    for fav in to_process:
        if fav.url[:5] != "data:":
            result = await is_reachable_async(
                fav.url, head_optim=False, include_response=True, client=client
            )

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
                    img_format = img.format
                    if img_format is not None:
                        img_format = img_format.lower()

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
                if img_format is not None:
                    img_format = img_format.lower()

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

        # If we are in these modes, we need to exit the for loop
        if mode in ["biggest", "smallest"]:
            break

        # Wait before next request to avoid detection
        time.sleep(sleep_time)

    real_favicons = sorted(
        real_favicons, key=lambda x: x.width * x.height, reverse=sort.lower() == "desc"
    )

    return real_favicons


async def guess_size(favicon: Favicon, chunk_size: int = 512) -> Tuple[int, int]:
    """Get size of image by requesting first bytes.

    Args:
        chunk_size: bytes size to iterate over image stream.

    Returns:
        The guessed width and height
    """
    async with httpx.stream("GET", favicon.url) as response:
        if (
            200 <= response.status_code < 300
            and "image" in response.headers["content-type"]
        ):
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
                    break

    width = height = 0
    if img is not None:
        width, height = img.size

    return width, height


async def guess_missing_sizes(
    favicons: Union[list[Favicon], set[Favicon]], chunk_size=512, sleep_time: int = 1
) -> list[Favicon]:
    favs = list(favicons)

    for idx in range(len(favs)):
        if (favs[idx].width == 0 or favs[idx].height == 0) and (
            favs[idx].reachable is None or favs[idx].reachable is True
        ):
            width, height = await guess_size(favs[idx], chunk_size=chunk_size)
            favs[idx] = favs[idx]._replace(width=width, height=height)
            time.sleep(sleep_time)

    return favs


async def check_availability(
    favicons: Union[list[Favicon], set[Favicon]],
    sleep_time: int = 1,
    client: Optional[AsyncClient] = None,
):
    favs = list(favicons)

    for idx in range(len(favs)):
        result = await is_reachable_async(favs[idx].url, head_optim=True, client=client)

        if result["success"] is True:
            favs[idx] = favs[idx]._replace(reachable=True)

        # If has been redirected
        if "redirect" in result:
            favs[idx] = favs[idx]._replace(url=result.get("final_url", favs[idx].url))

        time.sleep(sleep_time)

    return favs
