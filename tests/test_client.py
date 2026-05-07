import pytest
import httpx
from unittest.mock import MagicMock
from weather_api.client import get_weather


def test_get_weather_returns_parsed_data(mock_httpx_get, mock_weather_response):
    mock_httpx_get.return_value.json.return_value = mock_weather_response
    result = get_weather("Valencia")
    assert result["city"] == "Valencia"
    assert result["temperature"] == 18.5
    assert result["description"] == "clear sky"


def test_get_weather_raises_without_key(monkeypatch):
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENWEATHER_API_KEY"):
        get_weather("Valencia")


def test_get_weather_raises_on_http_error(mock_httpx_get):
    mock_httpx_get.return_value.raise_for_status.side_effect = (
        httpx.HTTPStatusError("401", request=MagicMock(), response=MagicMock())
    )
    with pytest.raises(httpx.HTTPStatusError):
        get_weather("Valencia")
