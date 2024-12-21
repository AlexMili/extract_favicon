# Extract Favicon

---

**Documentation**: <a href="https://alexmili.github.io/extract_favicon" target="_blank">https://alexmili.github.io/extract_favicon</a>

**Source Code**: <a href="https://github.com/alexmili/extract_favicon" target="_blank">https://github.com/alexmili/extract_favicon</a>

---

**Extract Favicon** is designed to easily retrieve favicons from any website. Built atop robust `reachable` and `BeautifulSoup`, it aims to deliver accurate and efficient favicon extraction for web scraping and data analysis workflows.

Key features include:

* **Automatic Extraction**: Detects multiple favicon references like `<link>`, `<meta>` and inline base64-encoded icons.
* **Smart Fallbacks**: When explicit icons aren’t defined, it checks standard fallback routes (like `favicon.ico`) to provide consistent results even on sites without standard declarations.
* **Size Guessing**: Dynamically determines favicon dimensions, even for images lacking explicit size information, by partially downloading and parsing their headers.
* **Base64 Support**: Easily handles inline data URLs, decoding base64-encoded images and validating them on-the-fly.
* **Availability Checks**: Validates each favicon’s URL, following redirects and marking icons as reachable or not.
* **DuckDuckGo Support**: Downloads Favicon directly from DuckDuckGo's public favicon API.
* **Google Support**: Downloads Favicon directly from Google's public favicon API.
* **Custom Strategy**: Sets the order in which the different available techniques are used to retrieve the best favicon.
* **Generate Favicon**: Generate a default SVG favicon when none are available.
* **Get Best Favicon**: Easily gets the best Favicon available, generate one if none are found.
* **Async Support**: Offers asynchronous methods (via `asyncio`) to efficiently handle multiple favicon extractions concurrently, enhancing overall performance when dealing with numerous URLs.

## Installation

Create and activate a virtual environment and then install `extract_favicon`:

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
```


## Inspiration
This library is an extension of the [favicon](https://github.com/scottwernervt/favicon/) package.
