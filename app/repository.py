from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Genre, Tag, Work, YouTubeSource


@dataclass
class WorkPage:
    items: list[Work]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)


def _base_query(public_only: bool = True) -> Select[tuple[Work]]:
    query = select(Work).options(
        joinedload(Work.source), selectinload(Work.genres), selectinload(Work.tags)
    )
    if public_only:
        query = query.where(
            Work.is_published.is_(True),
            Work.is_available.is_(True),
            Work.is_in_playlist.is_(True),
        )
    return query


def list_works(
    session: Session,
    *,
    q: str | None = None,
    content_type: str | None = None,
    length: str | None = None,
    genre: str | None = None,
    tag: str | None = None,
    year: int | None = None,
    page: int = 1,
    page_size: int = 24,
    sort: str = "playlist",
    public_only: bool = True,
) -> WorkPage:
    query = _base_query(public_only)
    source_joined = False
    if q:
        needle = f"%{q.strip()}%"
        query = query.outerjoin(YouTubeSource).where(
            or_(
                Work.title_override.ilike(needle),
                Work.original_title.ilike(needle),
                Work.synopsis.ilike(needle),
                YouTubeSource.title.ilike(needle),
                YouTubeSource.description.ilike(needle),
            )
        )
        source_joined = True
    if content_type:
        query = query.where(Work.content_type == content_type)
    if length:
        query = query.where(Work.length_category == length)
    if year:
        query = query.where(Work.year == year)
    if genre:
        query = query.join(Work.genres).where(Genre.slug == genre)
    if tag:
        query = query.join(Work.tags).where(Tag.slug == tag)

    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total = int(session.scalar(count_query) or 0)
    if sort == "title":
        if not source_joined:
            query = query.outerjoin(YouTubeSource)
            source_joined = True
        query = query.order_by(func.coalesce(Work.title_override, YouTubeSource.title).asc())
    elif sort == "year":
        query = query.order_by(Work.year.desc().nullslast(), Work.id.desc())
    else:
        if not source_joined:
            query = query.outerjoin(YouTubeSource)
        query = query.order_by(YouTubeSource.playlist_position.asc().nullslast(), Work.id.desc())
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    items = (
        session.scalars(query.distinct().offset((page - 1) * page_size).limit(page_size))
        .unique()
        .all()
    )
    return WorkPage(items=list(items), total=total, page=page, page_size=page_size)


def facets(session: Session) -> dict[str, list[dict[str, object]]]:
    public_filters = (
        Work.is_published.is_(True),
        Work.is_available.is_(True),
        Work.is_in_playlist.is_(True),
    )
    types = session.execute(
        select(Work.content_type, func.count(Work.id))
        .where(*public_filters)
        .group_by(Work.content_type)
        .order_by(Work.content_type)
    ).all()
    lengths = session.execute(
        select(Work.length_category, func.count(Work.id))
        .where(*public_filters)
        .group_by(Work.length_category)
        .order_by(Work.length_category)
    ).all()
    genres = session.execute(
        select(Genre.slug, Genre.name, func.count(Work.id))
        .join(Genre.works)
        .where(*public_filters)
        .group_by(Genre.id)
        .order_by(Genre.name)
    ).all()
    years = session.execute(
        select(Work.year, func.count(Work.id))
        .where(*public_filters, Work.year.is_not(None))
        .group_by(Work.year)
        .order_by(Work.year.desc())
    ).all()
    return {
        "types": [{"value": value, "count": count} for value, count in types],
        "lengths": [{"value": value, "count": count} for value, count in lengths],
        "genres": [{"value": slug, "label": name, "count": count} for slug, name, count in genres],
        "years": [{"value": value, "count": count} for value, count in years],
    }
