# Guía del Instructor

---

## Antes de clase

- Verificar que Docker Desktop está corriendo
- Tener el repo `weather-api-mini` creado en GitHub
- Tener el código base commiteado y pusheado
- Verificar que `OPENWEATHER_API_KEY` funciona:
  ```bash
  curl "https://api.openweathermap.org/data/2.5/weather?q=Valencia&appid=TU_KEY&units=metric"
  ```
- Tener el `.env` con la key real configurado localmente
- Hacer `docker compose up --build -d` una vez antes de clase
  para que todas las imágenes estén descargadas y en caché

---

## Problemas frecuentes

**`docker: permission denied`**
El usuario no está en el grupo `docker` (Linux).
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**`port already in use` en el puerto 8000**
Algo ya usa ese puerto en el host.
```bash
# Ver qué proceso usa el puerto
lsof -i :8000        # Linux/macOS
netstat -ano | findstr :8000  # Windows
```
Solución rápida: cambiar el puerto en `docker-compose.yml` a `"8001:8000"`.

**Redis connection refused en tests**
Verificar que el mock está activo — los tests no deben conectarse a Redis real.
El fixture `mock_redis` en `conftest.py` parchea `get_redis_client`.
Si el error persiste, el test no está usando el fixture.

**GitHub Actions falla en checkout**
Verificar que el repo es público o que el workflow tiene permisos de lectura.
En repos privados: `Settings → Actions → General → Workflow permissions → Read`.

**`uv sync --frozen` falla en el Dockerfile**
El `uv.lock` no está en el contexto de build. Verificar que `.dockerignore`
no excluye `uv.lock`. El archivo debe estar en el repo y commiteado.

---

## El momento del cache en vivo

Este es el momento más impactante de la clase. Ejecutar en orden:

```bash
# Primera consulta — llama a OpenWeather, guarda en Redis
curl "http://localhost:8000/weather?city=Valencia"
# → {"city": "Valencia", "temperature": 18.5, ..., "cached": false}

# Segunda consulta — devuelve desde Redis sin llamar a la API
curl "http://localhost:8000/weather?city=Valencia"
# → {"city": "Valencia", "temperature": 18.5, ..., "cached": true}
```

Luego entrar al contenedor Redis con redis-cli y mostrar la key almacenada:

```bash
# Ver todas las keys en Redis
docker compose exec redis redis-cli keys "*"
# → "weather:valencia"

# Ver el valor almacenado
docker compose exec redis redis-cli get "weather:valencia"
# → {"city": "Valencia", "temperature": 18.5, "description": "clear sky"}

# Ver el TTL restante — demuestra que el cache expira automáticamente
docker compose exec redis redis-cli ttl "weather:valencia"
# → 287 (segundos restantes)
```

Preguntar al alumno: *"¿Qué pasa cuando el TTL llega a cero?"*
Respuesta: Redis elimina la key y la próxima consulta vuelve a llamar a OpenWeather.

---

## Demostrar el CI roto y arreglado

Secuencia para mostrar el pipeline en acción:

```bash
# 1. Push limpio → check verde en GitHub
git push origin main
# Abrir GitHub → pestaña Actions → ver el job corriendo en tiempo real

# 2. Introducir un error de lint intencionalmente
# En client.py, agregar al final:
# import os  ← import duplicado, ruff lo detecta
git add src/weather_api/client.py
git commit -m "wip: break lint on purpose"
git push origin main
# Ver el check rojo en GitHub → Lint con ruff falla

# 3. Corregir el error
# Eliminar la línea añadida
git add src/weather_api/client.py
git commit -m "fix: remove duplicate import"
git push origin main
# Ver el check verde de nuevo
```

El objetivo es que el alumno vea el ciclo completo: push → CI falla → fix → CI pasa.

---

## Punto de corte si el tiempo se agota

**Mínimo indispensable:** Dockerfile funcionando + `docker compose up`.
El alumno debe salir con los contenedores corriendo y el cache demostrado.

**GitHub Actions puede quedar como tarea:**
El `ci.yml` ya está en el repo — el alumno solo necesita hacer un push para verlo correr.
Instrucción de tarea: *"Haz un push a tu repo y abre la pestaña Actions en GitHub."*

---

## Tiempos de referencia por bloque

| Bloque | Tiempo ideal | Señal de alerta |
|--------|-------------|-----------------|
| Introducción + Redis | 15 min | > 20 min → acortar ejemplos Redis |
| Explorar código base | 10 min | > 15 min → pasar directo al Dockerfile |
| Dockerfile | 30 min | > 40 min → saltar explicación de capas, ir al build |
| Docker Compose | 25 min | > 35 min → saltar demo redis-cli, ir directo al CI |
| GitHub Actions | 25 min | > 30 min → dejar como tarea |
| Demo + cierre | 15 min | no comprimir — es el momento de mayor impacto |
