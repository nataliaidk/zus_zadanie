import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.params_service import ParamsService


@pytest.fixture
def params() -> dict:
    return ParamsService().get()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
