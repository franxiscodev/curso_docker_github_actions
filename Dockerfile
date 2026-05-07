# Imagen base: Python 3.12 mínima
# "slim" = sin herramientas extras — imagen más pequeña y segura
FROM python:3.12-slim

# Directorio de trabajo dentro del contenedor
# Todos los COPY y RUN siguientes operan desde aquí
WORKDIR /app

# Instalar UV desde su imagen oficial
# COPY --from copia un archivo de otra imagen sin descargarla completa
# /uv y /uvx son los dos binarios del gestor de paquetes
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copiar SOLO los archivos de dependencias primero
# Si el código cambia pero las deps no → Docker reutiliza esta capa
# Principio clave: lo que cambia menos va antes
COPY pyproject.toml uv.lock ./

# Instalar dependencias sin instalar el proyecto todavía
# --frozen: usar exactamente las versiones del uv.lock (sin resolver)
# --no-install-project: no copiar src/ todavía — la capa de deps queda aislada
RUN uv sync --frozen --no-install-project

# Copiar el código fuente
# Va DESPUÉS de las deps — cambiar el código no invalida el cache de deps
# Docker reutiliza las capas anteriores y solo re-ejecuta desde aquí
COPY src/ ./src/

# Puerto que expone la aplicación
# Documentación — no abre el puerto en el host, solo lo declara
EXPOSE 8000

# Comando para arrancar el servidor
# 0.0.0.0 = aceptar conexiones desde fuera del contenedor
# Sin esto solo aceptaría conexiones desde dentro del contenedor
CMD ["uv", "run", "uvicorn", "weather_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
