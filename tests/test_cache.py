from weather_api.cache import get_cached_weather, set_cached_weather
import json


def test_cache_miss_returns_none(mock_redis):
    mock_redis.get.return_value = None
    result = get_cached_weather("Valencia")
    assert result is None
    mock_redis.get.assert_called_once_with("weather:valencia")


def test_cache_hit_returns_data(mock_redis):
    data = {"city": "Valencia", "temperature": 18.5, "description": "clear sky"}
    mock_redis.get.return_value = json.dumps(data)
    result = get_cached_weather("Valencia")
    assert result == data
