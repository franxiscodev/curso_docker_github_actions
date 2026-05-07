import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_weather_response():
    return {
        "main": {"temp": 18.5},
        "weather": [{"description": "clear sky"}],
        "name": "Valencia",
    }


@pytest.fixture
def mock_httpx_get(mocker, monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    mock = mocker.patch("weather_api.client.httpx.get")
    mock.return_value.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_redis(mocker):
    """Mock de Redis — tests sin servidor Redis real."""
    mock = mocker.patch("weather_api.cache.get_redis_client")
    mock_client = MagicMock()
    mock.return_value = mock_client
    return mock_client
