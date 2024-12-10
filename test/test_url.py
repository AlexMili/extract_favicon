import pytest

import extract_favicon


@pytest.mark.parametrize("url", ["https://www.python.org"], ids=["Python.org"])
def test_url(url):
    favicons = extract_favicon.from_url(url)
    assert len(favicons) == 6


def test_guessing_size():
    url = "https://www.python.org"
    favicons = extract_favicon.from_url(url)
    favicons = extract_favicon.check_availability(favicons)
    favicons = extract_favicon.guess_missing_sizes(favicons)
