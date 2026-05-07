"""Cache Redis para respuestas de OpenWeather."""
import json
import os
import redis

CACHE_TTL = 300  # 5 minutos


def get_redis_client() -> redis.Redis:
    """Crea cliente Redis desde variables de entorno."""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )


def get_cached_weather(city: str) -> dict | None:
    """Busca el clima de una ciudad en cache.

    Returns:
        Dict con los datos si existe en cache, None si no.
    """
    client = get_redis_client()
    data = client.get(f"weather:{city.lower()}")
    return json.loads(data) if data else None


def set_cached_weather(city: str, data: dict) -> None:
    """Guarda el clima de una ciudad en cache por CACHE_TTL segundos."""
    client = get_redis_client()
    client.setex(
        f"weather:{city.lower()}",
        CACHE_TTL,
        json.dumps(data),
    )
