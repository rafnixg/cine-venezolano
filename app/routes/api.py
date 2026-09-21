from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database import get_db
from app.models import Work
from app.presentation import work_dict
from app.repository import facets, list_works

router = APIRouter(prefix="/api/v1", tags=["catalog"])


def _optional_year(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    cleaned = value.strip()
    if not cleaned.isdigit():
        raise HTTPException(status_code=422, detail="El año debe ser un número entero")
    return int(cleaned)


@router.get("/works")
def api_works(
    q: str | None = None,
    type: str | None = None,
    length: str | None = None,
    genre: str | None = None,
    tag: str | None = None,
    year: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    sort: str = Query("playlist", pattern="^(playlist|title|year)$"),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = list_works(
        db,
        q=q,
        content_type=type,
        length=length,
        genre=genre,
        tag=tag,
        year=_optional_year(year),
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return {
        "items": [work_dict(work) for work in result.items],
        "pagination": {
            "page": result.page,
            "page_size": result.page_size,
            "pages": result.pages,
            "total": result.total,
        },
    }


@router.get("/works/{slug}")
def api_work(slug: str, db: Session = Depends(get_db)) -> dict[str, object]:
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
    return work_dict(work, detailed=True)


@router.get("/facets")
def api_facets(db: Session = Depends(get_db)) -> dict[str, object]:
    return facets(db)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
