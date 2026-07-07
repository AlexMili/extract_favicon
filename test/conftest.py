import pytest


@pytest.fixture(scope="function")
def base64_img() -> str:
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="


@pytest.fixture(scope="function")
def percent_encoded_svg_img() -> str:
    return (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'"
        " viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30'"
        " fill='%234285F4'/%3E%3Ctext x='32' y='42' font-size='32'"
        " text-anchor='middle' fill='white'"
        " font-family='Arial,sans-serif'%3EC%3C/text%3E%3C/svg%3E"
    )


@pytest.fixture(scope="function")
def svg_url() -> str:
    return "https://upload.wikimedia.org/wikipedia/commons/c/c3/Flag_of_France.svg"


@pytest.fixture(scope="function")
def gif_url() -> str:
    return "https://www.google.com/logos/doodles/2024/seasonal-holidays-2024-6753651837110333.2-la202124.gif"


@pytest.fixture(scope="function")
def python_url() -> str:
    return "https://www.python.org"
