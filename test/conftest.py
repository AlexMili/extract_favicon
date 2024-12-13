import pytest


@pytest.fixture(scope="function")
def base64_img():
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="


@pytest.fixture(scope="function")
def svg_url():
    return "https://upload.wikimedia.org/wikipedia/commons/c/c3/Flag_of_France.svg"


@pytest.fixture(scope="function")
def gif_url():
    return "https://www.google.com/logos/doodles/2024/seasonal-holidays-2024-6753651837110333.2-la202124.gif"


@pytest.fixture(scope="function")
def python_url():
    return "https://www.python.org"
