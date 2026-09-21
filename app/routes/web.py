from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database import get_db
from app.models import Work
from app.presentation import work_dict
from app.repository import facets, list_works
from app.services.classifier import CONTENT_LABELS, LENGTH_LABELS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _optional_year(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    cleaned = value.strip()
    if not cleaned.isdigit():
        raise HTTPException(status_code=422, detail="El año debe ser un número entero")
    return int(cleaned)


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    q: str | None = None,
    type: str | None = None,
    length: str | None = None,
    genre: str | None = None,
    year: str | None = None,
    page: int = 1,
    sort: str = "playlist",
    db: Session = Depends(get_db),
) -> HTMLResponse:
    parsed_year = _optional_year(year)
    safe_sort = sort if sort in {"playlist", "title", "year"} else "playlist"
    result = list_works(
        db,
        q=q,
        content_type=type,
        length=length,
        genre=genre,
        year=parsed_year,
        page=page,
        sort=safe_sort,
    )
    active = {
        "q": q or None,
        "type": type or None,
        "length": length or None,
        "genre": genre or None,
        "year": parsed_year,
        "sort": safe_sort,
    }
    pagination_query = urlencode(
        {
            key: value
            for key, value in active.items()
            if value is not None and value != "" and key != "page"
        }
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "works": [work_dict(work) for work in result.items],
            "pagination": result,
            "facets": facets(db),
            "active": active,
            "content_labels": CONTENT_LABELS,
            "length_labels": LENGTH_LABELS,
            "pagination_query": pagination_query,
        },
    )


@router.get("/obras/{slug}", response_class=HTMLResponse)
def detail(request: Request, slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    work = db.scalar(
        select(Work)
        .options(
            joinedload(Work.source),
            selectinload(Work.genres),
            selectinload(Work.tags),
            selectinload(Work.credits),
        )
        .where(
            Work.slug == slug,
            Work.is_published.is_(True),
            Work.is_available.is_(True),
            Work.is_in_playlist.is_(True),
        )
    )
    if not work:
        raise HTTPException(status_code=404, detail="Obra no encontrada")
    related = (
        db.scalars(
            select(Work)
            .options(joinedload(Work.source), selectinload(Work.genres), selectinload(Work.tags))
            .where(
                Work.id != work.id,
                Work.content_type == work.content_type,
                Work.is_published.is_(True),
                Work.is_available.is_(True),
                Work.is_in_playlist.is_(True),
            )
            .order_by(Work.year.desc().nullslast())
            .limit(4)
        )
        .unique()
        .all()
    )
    return templates.TemplateResponse(
        request,
        "detail.html",
        {
            "work": work_dict(work, detailed=True),
            "related": [work_dict(item) for item in related],
        },
    )
