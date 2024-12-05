# Extract Favicon

`extract-favicon` is a Python library to find and extract the favicon of any website.

## Installation

```bash
pip install favicon-extract
```

## Usage

```console
>>> import extract_favicon
>>> icons = extract_favicon.from_html(my_html, root_url="https://www.python.org/static/")
Icon(url='https://www.python.org/static/apple-touch-icon-144x144-precomposed.png', width=144, height=144, format='png')
Icon(url='https://www.python.org/static/apple-touch-icon-114x114-precomposed.png', width=114, height=114, format='png')
Icon(url='https://www.python.org/static/apple-touch-icon-72x72-precomposed.png', width=72, height=72, format='png')
Icon(url='https://www.python.org/static/apple-touch-icon-precomposed.png', width=0, height=0, format='png')
Icon(url='https://www.python.org/static/favicon.ico', width=0, height=0, format='ico')
```

## Inspiration
This library is an extension of the [favicon](https://github.com/scottwernervt/favicon/) package.
