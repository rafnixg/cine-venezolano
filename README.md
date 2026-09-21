# Cine Venezolano

[![CI](https://github.com/rafnixg/cine-venezolano/actions/workflows/ci.yml/badge.svg)](https://github.com/rafnixg/cine-venezolano/actions/workflows/ci.yml)
[![CodeQL](https://github.com/rafnixg/cine-venezolano/actions/workflows/codeql.yml/badge.svg)](https://github.com/rafnixg/cine-venezolano/actions/workflows/codeql.yml)
[![Container](https://github.com/rafnixg/cine-venezolano/actions/workflows/container.yml/badge.svg)](https://github.com/rafnixg/cine-venezolano/actions/workflows/container.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

Catálogo web en español para organizar y descubrir las obras de la playlist pública **CINE VENEZOLANO**. La aplicación conserva una copia local de los metadatos, ofrece búsqueda y filtros, y carga el reproductor de YouTube solamente cuando el visitante decide reproducir una obra.

## Origen y créditos

Este proyecto está basado en la playlist pública [🎬 CINE VENEZOLANO 🇻🇪✨](https://www.youtube.com/playlist?list=PLVQ42obHL2u_nJgblVTpWs3NQdD_WZkAM), creada y curada por [Daniela Carrión](https://www.youtube.com/@danielacarryon). Su trabajo de recopilación hace posible descubrir desde un mismo lugar películas, cortometrajes y documentales venezolanos disponibles en YouTube.

La aplicación organiza y presenta esa selección, pero no reclama autoría sobre la playlist ni sobre las obras enlazadas. Cada video pertenece a su respectivo canal, creador o titular de derechos.

## Stack

- FastAPI, SQLAlchemy y SQLite
- Jinja2 con HTML, CSS y JavaScript vanilla
- YouTube Data API v3 para sincronización
- APScheduler para la actualización semanal
- Docker para despliegue en un único servicio

## Inicio rápido

1. Crea un entorno virtual e instala dependencias:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

2. Copia `.env.example` como `.env` y configura `YOUTUBE_API_KEY`, `SESSION_SECRET` y `ADMIN_PASSWORD_HASH`. Genera el hash sin guardar la contraseña en el historial:

   ```powershell
   python -m app.cli hash-password
   ```

3. Inicializa y carga el catálogo:

   ```powershell
   alembic upgrade head
   python -m app.cli sync-youtube
   uvicorn app.main:app --reload
   ```

Abre `http://localhost:8000`. El panel está en `/admin` y la documentación de la API en `/docs`.

## Docker

Después de crear `.env`:

```powershell
docker compose build
docker compose up -d
docker compose exec web python -m app.cli sync-youtube
```

SQLite se guarda en el volumen `cine_data`. El contenedor aplica migraciones al iniciar.

La imagen verificada de cada cambio en `main` se publica en GitHub Container Registry:

```powershell
docker pull ghcr.io/rafnixg/cine-venezolano:latest
docker run --rm -p 8000:8000 ghcr.io/rafnixg/cine-venezolano:latest
```

También se generan etiquetas inmutables `sha-<commit>`. Los tags Git `v*` publican además
la versión correspondiente, por ejemplo `1.2.0` y `1.2` para `v1.2.0`.

## Comandos

- `python -m app.cli init-db`: crea tablas para desarrollo rápido.
- `python -m app.cli sync-youtube`: importa o actualiza toda la playlist.
- `python -m app.cli classify-metadata`: completa categorías vacías sin reemplazar la edición manual.
- `python -m pytest`: ejecuta las pruebas.
- `python -m ruff check .`: valida estilo y errores estáticos.
- `alembic upgrade head`: aplica migraciones pendientes.

## Integración continua

Los pull requests y cambios en `main` ejecutan Ruff, validación de JavaScript, pytest con cobertura mínima de 70% y una migración completa sobre SQLite. Workflows separados ejecutan CodeQL para Python, JavaScript y GitHub Actions; revisan dependencias nuevas de severidad alta; y construyen el contenedor con comprobaciones HTTP de la portada, el panel y el health check. Dependabot revisa semanalmente dependencias Python, Docker y GitHub Actions.

La sincronización automática corre cada domingo a las 03:00 en `America/Caracas`. Puede ajustarse mediante las variables `SYNC_*`. Los campos editoriales nunca son reemplazados por la sincronización.

## API pública

- `GET /api/v1/works`: catálogo paginado; acepta `q`, `type`, `length`, `genre`, `tag`, `year`, `decade`, `sort`, `page` y `page_size`.
- `GET /api/v1/works/{slug}`: ficha completa.
- `GET /api/v1/facets`: valores y conteos disponibles para filtros.
- `GET /api/v1/health`: comprobación básica del servicio.

No se descargan videos. Los elementos retirados de la playlist se ocultan sin borrar la curaduría local, y los datos de API que no puedan validarse durante 30 días se purgan.

## Licencia

Copyright © 2026, colaboradores de Cine Venezolano.

Este proyecto se distribuye bajo la [GNU Affero General Public License, versión 3 o posterior](LICENSE). Si modificas el software y lo ofreces a usuarios a través de una red, debes poner a su disposición el código fuente correspondiente de tu versión modificada, conforme a la sección 13 de la licencia.
