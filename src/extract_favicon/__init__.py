import os.path as osp

from .main import from_html


__all__ = ["from_html"]

version_path = osp.join(osp.dirname(__file__), "VERSION.md")
if osp.exists(version_path):
    with open(version_path, "r") as f:
        __version__ = f.readline()
