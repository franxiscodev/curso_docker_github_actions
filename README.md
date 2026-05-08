# weather-api-mini

Proyecto de clase para aprender **Docker Compose y GitHub Actions** desde cero.

## ¿De qué va?

Un microservicio FastAPI que consulta el clima de cualquier ciudad usando la API de OpenWeather y cachea las respuestas en Redis para evitar llamadas repetidas.

La primera consulta llama a la API externa. Las siguientes devuelven el resultado guardado en Redis durante 5 minutos — sin tocar la API.

El código Python ya está listo. El foco de la clase es 100% en Docker y CI.

## Tecnologías

- **FastAPI** — API REST con un solo endpoint `/weather`
- **Redis** — cache en memoria con TTL de 5 minutos
- **Docker Compose** — orquesta ambos servicios con un solo comando
- **GitHub Actions** — pipeline de CI que verifica lint y tests en cada push

## Requisitos Previos

- Docker Desktop instalado y corriendo
- Una API key de [OpenWeather](https://openweathermap.org/api) (cuenta gratuita)

## Arrancar el proyecto

```bash
# 1. Copiar el archivo de variables de entorno
cp .env.example .env

# 2. Añadir tu API key en .env
OPENWEATHER_API_KEY=tu_key_aqui

# 3. Levantar los servicios
docker compose up --build -d

# 4. Probar
curl "http://localhost:8000/weather?city=Valencia"
# {"city": "Valencia", "temperature": 18.5, "description": "clear sky", "cached": false}

curl "http://localhost:8000/weather?city=Valencia"
# {"city": "Valencia", "temperature": 18.5, "description": "clear sky", "cached": true}

# 5. Parar
docker compose down
```

## Estructura

```
weather-api-mini/
├── src/weather_api/       # código fuente (FastAPI + Redis)
├── tests/                 # tests con mocks (sin dependencias externas)
├── Dockerfile             # imagen de la API
├── docker-compose.yml     # FastAPI + Redis orquestados
└── .github/workflows/     # pipeline de CI
```
