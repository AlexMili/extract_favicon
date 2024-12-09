import pytest

import extract_favicon


@pytest.mark.parametrize("url", ["https://www.python.org"], ids=["Python.org"])
def test_url(url):
    favicons = extract_favicon.from_url(url)
    assert len(favicons) == 6
