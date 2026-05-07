# Teoría — Material del Instructor

Contenido profundo para estudiar antes de clase.

---

## Docker internals

### Namespaces Linux — aislamiento de procesos, red, filesystem

Docker no crea máquinas virtuales — usa características del kernel Linux.
Los namespaces aíslan recursos del sistema operativo entre procesos:

- **PID namespace**: el proceso dentro del contenedor ve su propio árbol de procesos.
  El PID 1 del contenedor es el proceso principal — si muere, el contenedor se detiene.
- **Network namespace**: cada contenedor tiene su propia interfaz de red, tabla de rutas
  e IP. Por eso dos contenedores pueden escuchar en el mismo puerto sin conflicto.
- **Mount namespace**: cada contenedor tiene su propio filesystem. Los cambios dentro
  no afectan al host.
- **UTS namespace**: cada contenedor puede tener su propio hostname.
- **IPC namespace**: aislamiento de memoria compartida entre procesos.
- **User namespace**: mapea usuarios del contenedor a usuarios del host (rootless Docker).

### cgroups — límites de CPU y memoria

Control Groups limitan cuántos recursos puede consumir un contenedor:

```bash
docker run --memory="256m" --cpus="0.5" weather-api-mini
```

Sin límites, un contenedor puede agotar la RAM del host y tumbar otros servicios.
En Kubernetes los `resources.limits` del Pod se traducen directamente a cgroups.

### Union filesystem — capas de imagen, copy-on-write

Una imagen Docker es una pila de capas de solo lectura.
Cuando se crea un contenedor, Docker añade una capa de escritura encima.

```
[capa escritura contenedor]  ← modificaciones en tiempo de ejecución
[capa 5: COPY src/]          ← código fuente
[capa 4: RUN uv sync]        ← dependencias instaladas
[capa 3: COPY pyproject.toml] ← archivos de configuración
[capa 2: WORKDIR /app]
[capa 1: python:3.12-slim]   ← imagen base
```

**Copy-on-write**: si el contenedor modifica un archivo de una capa inferior,
Docker copia ese archivo a la capa de escritura y lo modifica ahí.
Las capas originales nunca se modifican — se reutilizan entre contenedores.

### Por qué las imágenes Alpine son más pequeñas

Alpine Linux usa `musl libc` en lugar de `glibc` y `busybox` en lugar de GNU coreutils.
Resultado: imagen base de ~5 MB vs ~75 MB de Debian slim.

Trade-off: algunos paquetes Python con extensiones C pueden no compilar en Alpine
porque asumen `glibc`. Para aplicaciones Python puras, Alpine funciona bien.
`redis:7-alpine` pesa ~30 MB vs `redis:7` que pesa ~110 MB.

### Multi-stage builds — reducir el tamaño de la imagen final

Permite usar una imagen "grande" para compilar y copiar solo el resultado a una imagen mínima:

```dockerfile
# Etapa 1: compilar
FROM python:3.12 AS builder
RUN pip install build
COPY . .
RUN python -m build

# Etapa 2: imagen final mínima
FROM python:3.12-slim
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install /tmp/*.whl && rm /tmp/*.whl
```

La imagen final no contiene compiladores, headers ni archivos temporales.
Útil cuando se compilan extensiones C o se transpila TypeScript/Go.

---

## Redis internals

### Modelo single-threaded — por qué es tan rápido

Redis ejecuta comandos en un solo hilo. Sin locks, sin race conditions, sin overhead
de sincronización entre hilos. Cada comando se ejecuta atómicamente.

La velocidad viene de que todas las operaciones son en RAM — sin I/O de disco en el
camino crítico. Redis puede procesar ~100.000 operaciones/segundo en hardware modesto.

### Estructuras de datos: strings, hashes, lists, sets, sorted sets

Redis no es solo clave-valor de strings:

- **String**: `SET key value` — el tipo base, binario-safe hasta 512 MB
- **Hash**: `HSET user:1 name "Ana" age 30` — objeto con campos, eficiente en memoria
- **List**: `LPUSH queue job1` — lista enlazada, ideal para colas de tareas
- **Set**: `SADD tags python docker` — conjunto sin duplicados, operaciones de unión/intersección
- **Sorted Set**: `ZADD leaderboard 100 "player1"` — set ordenado por score, para rankings

En este proyecto usamos **String** con `SETEX` — el tipo más simple.

### TTL y expiración de keys

```
SETEX weather:valencia 300 '{"city": "Valencia", ...}'
TTL weather:valencia   → 287 (segundos restantes)
TTL weather:valencia   → -2  (key expirada y eliminada)
```

Redis elimina keys expiradas de forma lazy (cuando se accede) y en background periódicamente.
El TTL de 300 segundos en este proyecto garantiza que los datos no tengan más de 5 minutos de antigüedad.

### Persistencia: RDB vs AOF — cuándo usar cada una

Redis puede persistir datos en disco aunque es principalmente una base en memoria:

- **RDB (Redis Database)**: snapshot completo del dataset en un momento dado.
  Rápido de escribir y leer. Puede perder datos entre snapshots.
  Ideal para cache — si se pierde, se reconstruye.

- **AOF (Append Only File)**: log de todos los comandos de escritura.
  Más lento pero más seguro — pérdida máxima de 1 segundo.
  Ideal para datos que no se pueden perder.

**En este proyecto no usamos persistencia** — el cache es intencionadamente volátil.
Si Redis se reinicia, las ciudades se vuelven a consultar a OpenWeather. Correcto por diseño.

### Redis en producción: Sentinel, Cluster

- **Sentinel**: monitoriza instancias Redis, promueve réplica a primaria si la primaria falla.
  Alta disponibilidad sin sharding — todos los datos en cada nodo.

- **Cluster**: sharding automático de datos entre múltiples nodos.
  Escala horizontalmente — cada nodo tiene un subconjunto de las keys.
  Requiere cliente compatible (redis-py lo soporta).

---

## GitHub Actions

### El modelo de runners — VMs bajo demanda

Cada ejecución del workflow arranca una VM nueva en los servidores de GitHub.
`ubuntu-latest` es una VM con Ubuntu, Docker, Python, Node y muchas herramientas preinstaladas.

La VM se destruye al finalizar el job — no hay estado entre ejecuciones.
Esto garantiza reproducibilidad: el mismo código siempre produce el mismo resultado.

### Cache de dependencias entre runs

Sin cache, cada run instala todas las dependencias desde cero (~30 segundos).
Con cache, solo descarga lo que cambió:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: uv-${{ hashFiles('uv.lock') }}
```

El `key` cambia solo si `uv.lock` cambia — si las deps no cambiaron, la cache se reutiliza.
UV tiene su propio cache integrado con `astral-sh/setup-uv@v3`.

### Secrets de GitHub — cómo agregar la API key sin exponerla

Las variables de entorno en el YAML son visibles en el repo público.
Los Secrets se almacenan cifrados y solo se inyectan en tiempo de ejecución:

```
GitHub repo → Settings → Secrets and variables → Actions → New repository secret
Nombre: OPENWEATHER_API_KEY
Valor: tu_api_key_real
```

En el workflow:
```yaml
env:
  OPENWEATHER_API_KEY: ${{ secrets.OPENWEATHER_API_KEY }}
```

Los Secrets nunca aparecen en los logs — GitHub los enmascara automáticamente.

### Matrix builds — testear en múltiples versiones de Python

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]

steps:
  - run: uv python install ${{ matrix.python-version }}
```

GitHub ejecuta el job en paralelo para cada versión — tres runs simultáneos.
Útil para librerías que deben soportar múltiples versiones de Python.

### Workflow triggers: push, pull_request, schedule, workflow_dispatch

```yaml
on:
  push:
    branches: [main]           # en cada push a main
  pull_request:
    branches: [main]           # en cada PR contra main
  schedule:
    - cron: '0 8 * * 1'        # todos los lunes a las 8:00 UTC
  workflow_dispatch:            # trigger manual desde la UI de GitHub
```

`schedule` es útil para tests de integración nocturnos o verificar que deps externas siguen funcionando.
`workflow_dispatch` permite lanzar el workflow manualmente sin hacer un push.

---

## Referencias

- Docker docs: https://docs.docker.com
- Redis docs: https://redis.io/docs
- GitHub Actions docs: https://docs.github.com/actions
- Play with Docker: https://labs.play-with-docker.com
