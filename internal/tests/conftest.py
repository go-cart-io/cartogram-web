import pathlib

import pytest
from web import create_app


@pytest.fixture
def client():
    app = create_app()
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_data_dir():
    root = pathlib.Path(__file__).parent.parent.parent
    return root / "test-data"
