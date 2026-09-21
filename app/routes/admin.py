from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth import csrf_token, require_admin, validate_csrf, verify_admin_password
from app.config import settings
from app.database import get_db
from app.models import Credit, Genre, SyncRun, Tag, Work
from app.scheduler import run_configured_sync
from app.services.classifier import CONTENT_LABELS, LENGTH_LABELS, slugify

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


def _run_sync() -> None:
    run_configured_sync("admin")


def _terms(value: str) -> list[str]:
    return list(dict.fromkeys(term.strip() for term in value.split(",") if term.strip()))


def _taxonomy(db: Session, model: type[Genre] | type[Tag], values: list[str]):
    entities = []
    for value in values:
        slug = slugify(value)
        entity = db.scalar(select(model).where(model.slug == slug))
        if not entity:
            entity = model(name=value, slug=slug)
            db.add(entity)
        entities.append(entity)
    return entities


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    if request.session.get("is_admin"):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {"csrf_token": csrf_token(request), "configured": bool(settings.admin_password_hash)},
    )


@router.post("/login")
def login(
    request: Request,
    password: str = Form(...),
    csrf: str = Form(...),
) -> Response:
    validate_csrf(request, csrf)
    if verify_admin_password(password):
        request.session.clear()
        request.session["is_admin"] = True
        csrf_token(request)
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {
            "csrf_token": csrf_token(request),
            "configured": bool(settings.admin_password_hash),
            "error": "Contraseña incorrecta",
        },
        status_code=401,
    )


@router.post("/logout")
def logout(request: Request, csrf: str = Form(...)) -> RedirectResponse:
    require_admin(request)
    validate_csrf(request, csrf)
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    require_admin(request)
    works = (
        db.scalars(
            select(Work)
            .options(joinedload(Work.source))
            .order_by(Work.needs_review.desc(), Work.updated_at.desc())
        )
        .unique()
        .all()
    )
    runs = db.scalars(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(10)).all()
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "works": works,
            "runs": runs,
            "csrf_token": csrf_token(request),
            "youtube_configured": bool(settings.youtube_api_key),
        },
    )


@router.post("/sync")
def trigger_sync(
    request: Request,
    background_tasks: BackgroundTasks,
    csrf: str = Form(...),
) -> RedirectResponse:
    require_admin(request)
    validate_csrf(request, csrf)
    if not settings.youtube_api_key:
        raise HTTPException(status_code=503, detail="YOUTUBE_API_KEY no está configurada")
    background_tasks.add_task(_run_sync)
    return RedirectResponse("/admin?sync=started", status_code=303)


@router.get("/works/{work_id}", response_class=HTMLResponse)
def edit_page(request: Request, work_id: int, db: Session = Depends(get_db)) -> HTMLResponse:
    require_admin(request)
    work = db.scalar(
        select(Work)
        .options(
            joinedload(Work.source),
            selectinload(Work.genres),
            selectinload(Work.tags),
            selectinload(Work.credits),
        )
        .where(Work.id == work_id)
    )
    if not work:
        raise HTTPException(status_code=404, detail="Obra no encontrada")
    return templates.TemplateResponse(
        request,
        "admin/edit.html",
        {
            "work": work,
            "content_labels": CONTENT_LABELS,
            "length_labels": LENGTH_LABELS,
            "csrf_token": csrf_token(request),
        },
    )


@router.post("/works/{work_id}")
def edit_work(
    request: Request,
    work_id: int,
    csrf: str = Form(...),
    title: str = Form(""),
    original_title: str = Form(""),
    synopsis: str = Form(""),
    year: str = Form(""),
    country: str = Form("Venezuela"),
    language: str = Form(""),
    subtitles: str = Form(""),
    content_type: str = Form("other"),
    length_category: str = Form("unknown"),
    genres: str = Form(""),
    tags: str = Form(""),
    directors: str = Form(""),
    cast: str = Form(""),
    is_published: str | None = Form(None),
    reviewed: str | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    require_admin(request)
    validate_csrf(request, csrf)
    if content_type not in CONTENT_LABELS or length_category not in LENGTH_LABELS:
        raise HTTPException(status_code=422, detail="Clasificación inválida")
    work = db.get(Work, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Obra no encontrada")
    work.title_override = title.strip() or None
    work.original_title = original_title.strip() or None
    work.synopsis = synopsis.strip() or None
    work.year = int(year) if year.strip().isdigit() else None
    work.country = country.strip() or "Venezuela"
    work.language = language.strip() or None
    work.subtitles = subtitles.strip() or None
    work.content_type = content_type
    work.length_category = length_category
    work.is_published = is_published == "on"
    work.needs_review = reviewed != "on"
    work.genres = _taxonomy(db, Genre, _terms(genres))
    work.tags = _taxonomy(db, Tag, _terms(tags))
    work.credits.clear()
    for role, names in (("Dirección", _terms(directors)), ("Reparto", _terms(cast))):
        for position, name in enumerate(names):
            work.credits.append(Credit(role=role, name=name, position=position))
    db.commit()
    return RedirectResponse(f"/admin/works/{work_id}?saved=1", status_code=303)
