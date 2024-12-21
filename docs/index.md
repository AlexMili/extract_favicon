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

```console
$ pip install extract_favicon
```

## Usage


### Extracting Favicons from HTML

The `from_html` function allows you to parse a given HTML string and extract all favicons referenced within it. It looks for common `<link>` and `<meta>` tags that reference icons (e.g., `icon`, `shortcut icon`, `apple-touch-icon`, etc.). If `include_fallbacks` is set to `True`, it will also check standard fallback paths like `favicon.ico` when no icons are explicitly defined.

**Example:**
```python
html_content = """
<!DOCTYPE html>
<html>
<head>
  <link rel="icon" href="https://example.com/favicon.ico" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
</head>
<body>
  <p>Sample page</p>
</body>
</html>
"""

favicons = from_html(html_content, root_url="https://example.com", include_fallbacks=True)
for favicon in favicons:
    print(favicon.url, favicon.width, favicon.height)
```

### Extracting Favicons from a URL

If you only have a URL and want to directly extract favicons, `from_url` fetches the page, parses it, and returns a set of `Favicon` objects. It uses `Reachable` internally to check if the URL is accessible. If `include_fallbacks` is True, fallback icons (like `/favicon.ico`) are also considered.

```python
favicons = from_url("https://example.com", include_fallbacks=True)
for favicon in favicons:
    print(favicon.url, favicon.format, favicon.width, favicon.height)
```

### Downloading Favicons

Depending on the mode, you can choose to download:

* "all": Download all favicons.
* "biggest": Download only the largest favicon (by area).
* "smallest": Download only the smallest favicon.

If `include_unknown` is False, favicons without known dimensions are skipped. The `sort` option sorts the returned favicons by size, and `sleep_time` controls how long to wait between requests to avoid rate limits.

The result is a list of `RealFavicon` objects, which contain additional information like the loaded image or raw SVG data.

```python
favicons = from_url("https://example.com")
real_favicons = download(favicons, mode="all", sort="DESC")

for real_favicon in real_favicons:
    print(real_favicon.url.url, real_favicon.valid, real_favicon.width, real_favicon.height)
```

### Checking Favicon Availability

Sends a HEAD request for each favicon URL to determine if it’s reachable. If the favicon has been redirected, it updates the URL accordingly. It also sets the reachable attribute on each Favicon. The `sleep_time` parameter lets you pause between checks to reduce the load on the target server.

```python
favicons = from_url("https://example.com")
checked_favicons = check_availability(favicons)

for favicon in checked_favicons:
    print(favicon.url, favicon.reachable)
```

### Guessing Favicon Sizes

If some extracted favicons don’t have their dimensions specified, `guess_missing_sizes` can attempt to determine their width and height. For base64-encoded favicons (data URLs), setting `load_base64_img` to `True` allows the function to decode and load the image in memory to get its size. For external images, it partially downloads the image to guess its dimensions without retrieving the entire file.

```python
favicons = from_url("https://example.com")
# Some favicons may not have width/height info
favicons_with_sizes = guess_missing_sizes(favicons, load_base64_img=True)

for favicon in favicons_with_sizes:
    print(favicon.url, favicon.width, favicon.height)
```

### Generating a Favicon

The generate_favicon function builds a simple placeholder favicon in SVG format based on the first letter of the domain. It’s useful when other methods fail or if you need a fallback icon quickly.

```python
placeholder_favicon = generate_favicon("https://example.com")

# The Favicon object contains the SVG data as if it were a real icon.
print("Generated favicon URL:", placeholder_favicon.url)
```

### Get the Best Favicon Available

The `get_best_favicon` function tries multiple techniques in a specified order to find the best possible favicon. By default, the order is:

* `content`: Attempts to extract favicons from HTML or directly from the URL.
* `duckduckgo`: Fetches a favicon from DuckDuckGo if the first step fails.
* `google`: Retrieves a favicon from Google if the previous steps fails.
* `generate`: Generates a placeholder if no other method is successful.

The function returns the first valid favicon found or None if none is discovered.

```python
best_icon = get_best_favicon("https://example.com")

if best_icon:
    print("Best favicon URL:", best_icon.url)
    print("Favicon dimensions:", best_icon.width, "x", best_icon.height)
else:
    print("No valid favicon found for this URL.")
```

## Dependencies

When you install `extract_favicon` it comes with the following dependencies:

* <a href="https://www.crummy.com/software/BeautifulSoup" target="_blank"><code>BeautifulSoup</code></a> - to parse HTML content.
* <a href="https://github.com/python-pillow/Pillow" target="_blank"><code>Pillow</code></a> - to load images to get real size once downloaded and to guess image size based on its streamed headers.
* <a href="https://github.com/alexmili/reachable" target="_blank"><code>Reachable</code></a> - to check availability of favicons' URLs, download content and handle redirects, HTTP errors and some simple anti-bot protections.
* <a href="https://github.com/tiran/defusedxml" target="_blank"><code>DefusedXML</code></a> - to parse and check validity of SVG files.
* <a href="https://github.com/john-kurkowski/tldextract" target="_blank"><code>TLDextract</code></a> - to parse and extract domain information from URL.

## Inspiration
This library is an extension of the [favicon](https://github.com/scottwernervt/favicon/) package.

## License

This project is licensed under the terms of the MIT license.
