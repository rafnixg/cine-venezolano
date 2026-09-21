from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import admin, api, web
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Cine Venezolano",
    description="Catálogo curado de cine venezolano disponible en YouTube.",
    version="0.0.2",
    lifespan=lifespan,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    https_only=settings.session_https_only,
    same_site="lax",
    session_cookie="cine_admin",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api.router)
app.include_router(admin.router)
app.include_router(web.router)
