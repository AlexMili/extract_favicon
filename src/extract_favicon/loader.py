import base64
import io
import os
from typing import Optional, Tuple, Union
from urllib.parse import urlparse

import defusedxml.ElementTree as ETree
from PIL import Image, UnidentifiedImageError
from reachable import is_reachable, is_reachable_async
from reachable.client import AsyncClient, Client

from .config import Favicon, FaviconHttp
from .utils import _get_url


def load_image(favicon: Favicon, client: Optional[Client] = None) -> Favicon:
    if favicon.url[:5] == "data:":
        favicon = _load_base64_img(favicon)
    else:
        result = is_reachable(
            favicon.url, head_optim=False, include_response=True, client=client
        )

        fav_http = FaviconHttp(
            original_url=favicon.url,
            final_url=result.get("final_url", favicon.url),
            redirected="redirect" in result,
            status_code=result.get("status_code", -1),
        )

        favicon = favicon._replace(http=fav_http)

        if result["success"] is True:
            favicon = favicon._replace(reachable=True)
            filename = os.path.basename(urlparse(_get_url(favicon)).path)

            if filename.lower().endswith(".svg") is True:
                favicon = _load_svg_img(favicon, result["response"].content)
            else:
                favicon = _load_img(favicon, result["response"].content)
        else:
            favicon = favicon._replace(reachable=False)

    return favicon


async def load_image_async(
    favicon: Favicon, client: Optional[AsyncClient] = None
) -> Favicon:
    if favicon.url[:5] == "data:":
        favicon = _load_base64_img(favicon)
    else:
        result = await is_reachable_async(
            favicon.url, head_optim=False, include_response=True, client=client
        )

        fav_http = FaviconHttp(
            original_url=favicon.url,
            final_url=result.get("final_url", favicon.url),
            redirected="redirect" in result,
            status_code=result.get("status_code", -1),
        )

        favicon = favicon._replace(http=fav_http)

        if result["success"] is True:
            favicon = favicon._replace(reachable=True)
            filename = os.path.basename(urlparse(_get_url(favicon)).path)

            if filename.lower().endswith(".svg") is True:
                favicon = _load_svg_img(favicon, result["response"].content)
            else:
                favicon = _load_img(favicon, result["response"].content)
        else:
            favicon = favicon._replace(reachable=False)

    return favicon


def _open_and_verify_image(bytes_content: bytes) -> Tuple[Optional[Image.Image], bool]:
    """
    Loads an image from the provided byte content and verifies its validity.

    This function attempts to open and verify an image using the given
    byte content. If the image is valid, it returns the loaded `Image.Image`
    object and a boolean indicating successful validation. If the image is
    invalid or cannot be opened, it returns `None` for the image and `False`
    for the validity.

    Args:
        bytes_content: The byte content representing the image.

    Returns:
        A tuple where the first element  is the loaded `Image.Image` object if
        the image is valid, otherwise `None`, and the second element is a boolean
        indicating whether the image is valid.
    """
    is_valid: bool = False
    img: Optional[Image.Image] = None

    if len(bytes_content) > 0:
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


def _load_img(favicon: Favicon, bytes_content: bytes, force: bool = False) -> Favicon:
    if favicon.image is None or force is True:
        img, is_valid = _open_and_verify_image(bytes_content)
        width, height, img_format = _get_meta_image(img)

        favicon = favicon._replace(
            width=width,
            height=height,
            format=img_format,
            valid=is_valid,
            image=img,
        )

    return favicon


def _load_base64_img(favicon: Favicon, force: bool = False) -> Favicon:
    if favicon.image is None or force is True:
        data_img = favicon.url.split(",")
        suffix = (
            data_img[0]
            .replace("data:", "")
            .replace(";base64", "")
            .replace("image", "")
            .replace("/", "")
            .lower()
            .strip()
        )

        if len(data_img) > 1 and suffix in ["svg", "svg+xml"]:
            bytes_content = base64.b64decode(data_img[1])
            favicon = _load_svg_img(favicon, bytes_content)
        elif len(data_img) > 1:
            bytes_content = base64.b64decode(data_img[1])
            img, is_valid = _open_and_verify_image(bytes_content)
            width, height, img_format = _get_meta_image(img)

            favicon = favicon._replace(
                width=width,
                height=height,
                format=img_format,
                valid=is_valid,
                image=img,
                reachable=len(data_img[1]) > 0,
            )
        else:
            favicon = favicon._replace(valid=False)

    return favicon


def _load_svg_img(
    favicon: Favicon, bytes_content: Union[bytes, str], force: bool = False
) -> Favicon:
    if favicon.image is None or force is True:
        root = None

        try:
            root = ETree.fromstring(bytes_content)
        # TODO: find right exception
        except Exception:
            is_valid = False

        # Check if the root tag is SVG
        if root is not None and root.tag.lower().endswith("svg"):
            is_valid = True
        else:
            is_valid = False

        width = 0
        height = 0

        if root is not None and "width" in root.attrib:
            try:
                width = int(root.attrib["width"])
            except ValueError:
                pass

        if root is not None and "height" in root.attrib:
            try:
                height = int(root.attrib["height"])
            except ValueError:
                pass

        favicon = favicon._replace(
            width=width,
            height=height,
            format="svg",
            valid=is_valid,
            reachable=True,
        )

        if root is not None and is_valid is True:
            favicon = favicon._replace(image=ETree.tostring(root, encoding="utf-8"))

    return favicon


def _get_meta_image(img: Optional[Image.Image]) -> Tuple[int, int, Optional[str]]:
    width = height = 0
    img_format = None

    if img is not None:
        width, height = img.size
        if img.format is not None:
            img_format = img.format.lower()

    return width, height, img_format
