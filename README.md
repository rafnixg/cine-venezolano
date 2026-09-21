# Cine Venezolano

Catálogo web en español para organizar y descubrir las obras de la playlist pública **CINE VENEZOLANO**. La aplicación conserva una copia local de los metadatos, ofrece búsqueda y filtros, y carga el reproductor de YouTube solamente cuando el visitante decide reproducir una obra.

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

## Comandos

- `python -m app.cli init-db`: crea tablas para desarrollo rápido.
- `python -m app.cli sync-youtube`: importa o actualiza toda la playlist.
- `python -m pytest`: ejecuta las pruebas.
- `python -m ruff check .`: valida estilo y errores estáticos.
- `alembic upgrade head`: aplica migraciones pendientes.

La sincronización automática corre cada domingo a las 03:00 en `America/Caracas`. Puede ajustarse mediante las variables `SYNC_*`. Los campos editoriales nunca son reemplazados por la sincronización.

## API pública

- `GET /api/v1/works`: catálogo paginado; acepta `q`, `type`, `length`, `genre`, `tag`, `year`, `sort`, `page` y `page_size`.
- `GET /api/v1/works/{slug}`: ficha completa.
- `GET /api/v1/facets`: valores y conteos disponibles para filtros.
- `GET /api/v1/health`: comprobación básica del servicio.

No se descargan videos. Los elementos retirados de la playlist se ocultan sin borrar la curaduría local, y los datos de API que no puedan validarse durante 30 días se purgan.
