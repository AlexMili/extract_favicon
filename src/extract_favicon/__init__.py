import os.path as osp

from .main import check_availability, download, from_html, from_url, guess_missing_sizes


__all__ = [
    "check_availability",
    "download",
    "from_html",
    "from_url",
    "guess_missing_sizes",
]

version_path = osp.join(osp.dirname(__file__), "VERSION.md")
if osp.exists(version_path):
    with open(version_path, "r") as f:
        __version__ = f.readline()
