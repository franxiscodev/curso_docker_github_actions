"""API de clima con cache Redis."""

import httpx
from fastapi import FastAPI, HTTPException

from weather_api.cache import get_cached_weather, set_cached_weather
from weather_api.client import get_weather

app = FastAPI(title="Weather API Mini")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/weather")
def weather(city: str):
    """Devuelve el clima de una ciudad con cache Redis.

    La primera consulta llama a OpenWeather y guarda en Redis.
    Las siguientes consultas devuelven el resultado cacheado.
    """
    cached = get_cached_weather(city)
    if cached:
        return {**cached, "cached": True}

    try:
        data = get_weather(city)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

    set_cached_weather(city, data)

    return {**data, "cached": False}
