import os
from unittest.mock import MagicMock

import httpx
import pytest

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
    mock_httpx_get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401", request=MagicMock(), response=MagicMock()
    )
    with pytest.raises(httpx.HTTPStatusError):
        get_weather("Valencia")


# Solo corre en CI (GitHub Actions pone CI=true automáticamente)
# Localmente se salta — no requiere tener la key real para desarrollar
@pytest.mark.skipif(
    os.getenv("CI") != "true",
    reason="Solo corre en CI — verifica que el secret está configurado",
)
def test_api_key_configurada_en_ci():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    assert api_key, (
        "OPENWEATHER_API_KEY no configurada — pruebo de nuevo"
        "añádela en GitHub: Settings → Secrets and variables → Actions"
    )
