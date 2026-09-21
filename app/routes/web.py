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


def _optional_decade(value: str | None) -> int | None:
    parsed = _optional_year(value)
    if parsed is not None and (parsed < 1890 or parsed > 2100 or parsed % 10):
        raise HTTPException(status_code=422, detail="La década debe ser un múltiplo de diez")
    return parsed


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    q: str | None = None,
    type: str | None = None,
    length: str | None = None,
    genre: str | None = None,
    tag: str | None = None,
    year: str | None = None,
    decade: str | None = None,
    page: int = 1,
    sort: str = "playlist",
    db: Session = Depends(get_db),
) -> HTMLResponse:
    parsed_year = _optional_year(year)
    parsed_decade = _optional_decade(decade)
    safe_sort = sort if sort in {"playlist", "title", "year", "year_asc"} else "playlist"
    result = list_works(
        db,
        q=q,
        content_type=type,
        length=length,
        genre=genre,
        tag=tag,
        year=parsed_year,
        decade=parsed_decade,
        page=page,
        sort=safe_sort,
    )
    active = {
        "q": q or None,
        "type": type or None,
        "length": length or None,
        "genre": genre or None,
        "tag": tag or None,
        "year": parsed_year,
        "decade": parsed_decade,
        "sort": safe_sort,
    }
    facet_data = facets(db)
    label_maps = {
        "type": CONTENT_LABELS,
        "length": LENGTH_LABELS,
        "genre": {item["value"]: item["label"] for item in facet_data["genres"]},
        "tag": {item["value"]: item["label"] for item in facet_data["tags"]},
        "decade": {item["value"]: item["label"] for item in facet_data["decades"]},
    }
    active_filters = []
    for key in ("q", "type", "length", "genre", "tag", "decade", "year"):
        value = active.get(key)
        if value is None or value == "":
            continue
        label = f'“{value}”' if key == "q" else label_maps.get(key, {}).get(value, value)
        remaining = {
            name: current
            for name, current in active.items()
            if name != key and current is not None and current != ""
        }
        active_filters.append(
            {"label": str(label), "url": f"/?{urlencode(remaining)}" if remaining else "/"}
        )
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
            "facets": facet_data,
            "active": active,
            "active_filters": active_filters,
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
