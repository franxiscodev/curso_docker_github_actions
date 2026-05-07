"""Cliente de OpenWeather API."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city: str) -> dict:
    """Consulta el clima actual de una ciudad.

    Args:
        city: Nombre de la ciudad.

    Returns:
        Dict con city, temperature y description.

    Raises:
        ValueError: Si la API key no está configurada.
        httpx.HTTPError: Si la API devuelve un error.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY no configurada")

    response = httpx.get(
        BASE_URL,
        params={"q": city, "appid": api_key, "units": "metric"},
    )
    response.raise_for_status()
    data = response.json()

    match data:
        case {
            "main": {"temp": float(temp)},
            "weather": [{"description": str(desc)}, *_],
            "name": str(city_name),
        }:
            return {
                "city": city_name,
                "temperature": round(temp, 1),
                "description": desc,
            }
        case {"message": str(msg)}:
            raise ValueError(f"API error: {msg}")
        case _:
            raise ValueError(f"Respuesta inesperada: {data}")
