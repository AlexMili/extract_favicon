import pytest

import extract_favicon
from extract_favicon import main_async as ef_async


def test_url(python_url):
    favicons = extract_favicon.from_url(python_url)
    assert len(favicons) == 6


@pytest.mark.asyncio
async def test_url_async(python_url):
    favicons = await ef_async.from_url(python_url)
    assert len(favicons) == 6


def test_guessing_size(python_url):
    favicons = extract_favicon.from_url(python_url)
    favicons = extract_favicon.check_availability(favicons)
    favicons = extract_favicon.guess_missing_sizes(favicons)


@pytest.mark.asyncio
async def test_guessing_size_async(python_url):
    favicons = await ef_async.from_url(python_url)
    favicons = await ef_async.check_availability(favicons)
    favicons = await ef_async.guess_missing_sizes(favicons)


def test_unreachable_url():
    url = "https://random.trustlist.ai"
    favicons = extract_favicon.from_url(url)
    assert isinstance(favicons, set) is True
    assert len(favicons) == 0


@pytest.mark.asyncio
async def test_unreachable_url_async():
    url = "https://random.trustlist.ai"
    favicons = await ef_async.from_url(url)
    assert isinstance(favicons, set) is True
    assert len(favicons) == 0
