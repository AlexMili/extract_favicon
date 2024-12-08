# Extract Favicon

`extract-favicon` is a Python library to find and extract the favicon of any website.

## Installation

```bash
pip install extract_favicon
```

## Usage

```python
>>> import extract_favicon
>>> icons = extract_favicon.from_url("https://www.python.org/")
Favicon(url="https://www.python.org/static/apple-touch-icon-144x144-precomposed.png", width=144, height=144, format="png")
Favicon(url="https://www.python.org/static/apple-touch-icon-114x114-precomposed.png", width=114, height=114, format="png")
Favicon(url="https://www.python.org/static/apple-touch-icon-72x72-precomposed.png", width=72, height=72, format="png")
Favicon(url="https://www.python.org/static/apple-touch-icon-precomposed.png", width=0, height=0, format="png")
Favicon(url="https://www.python.org/static/favicon.ico", width=0, height=0, format="ico")
```

Directly from already downloaded HTML:
```python
>>> import extract_favicon
>>> icons = extract_favicon.from_html(my_html, root_url="https://www.python.org/static/")
Favicon(url="https://www.python.org/static/apple-touch-icon-144x144-precomposed.png", width=144, height=144, format="png")
Favicon(url="https://www.python.org/static/apple-touch-icon-114x114-precomposed.png", width=114, height=114, format="png")
Favicon(url="https://www.python.org/static/apple-touch-icon-72x72-precomposed.png", width=72, height=72, format="png")
Favicon(url="https://www.python.org/static/apple-touch-icon-precomposed.png", width=0, height=0, format="png")
Favicon(url="https://www.python.org/static/favicon.ico", width=0, height=0, format="ico")
```

Download extracted favicons:
```python
>>> import extract_favicon
>>> favicons = extract_favicon.from_html(my_html, root_url="https://www.python.org/static/")
>>> favicons_obj = extract_favicon.download(favicons)
[
    RealFavicon(
        url=FaviconURL(
            url="https://www.python.org/static/apple-touch-icon-precomposed.png",
            final_url="https://www.python.org/static/apple-touch-icon-precomposed.png",
            redirected=False,
            status_code=200,
        ),
        format="png",
        valid=True,
        original=Favicon(
            url="https://www.python.org/static/apple-touch-icon-precomposed.png",
            format="png",
            width=0,
            height=0,
        ),
        image=<PIL.PngImagePlugin.PngImageFile image mode=RGBA size=57x57>,
        width=57,
        height=57,
    )
]
```


## Inspiration
This library is an extension of the [favicon](https://github.com/scottwernervt/favicon/) package.
