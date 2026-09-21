from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Genre, Tag, Work
from app.services.classifier import infer_content_type, infer_genres, infer_tags, slugify


def _entities(session: Session, model: type[Genre] | type[Tag], names: list[str]):
    entities = []
    for name in names:
        slug = slugify(name)
        entity = next(
            (
                candidate
                for candidate in session.new
                if isinstance(candidate, model) and candidate.slug == slug
            ),
            None,
        )
        if entity is None:
            entity = session.scalar(select(model).where(model.slug == slug))
        if entity is None:
            entity = model(name=name, slug=slug)
            session.add(entity)
        entities.append(entity)
    return entities


def enrich_work(session: Session, work: Work, title: str, description: str = "") -> bool:
    """Fill empty inferred fields without replacing editorial metadata."""
    if not work.needs_review:
        return False

    changed = False
    if work.content_type == "other":
        inferred_type = infer_content_type(title, description)
        if inferred_type != "other":
            work.content_type = inferred_type
            changed = True
    if not work.genres:
        genres = infer_genres(title, description)
        if genres:
            work.genres = _entities(session, Genre, genres)
            changed = True
    if not work.tags:
        tags = infer_tags(title, description)
        if tags:
            work.tags = _entities(session, Tag, tags)
            changed = True
    return changed


def enrich_catalog(session: Session) -> int:
    works = (
        session.scalars(
            select(Work).options(
                joinedload(Work.source), selectinload(Work.genres), selectinload(Work.tags)
            )
        )
        .unique()
        .all()
    )
    updated = 0
    for work in works:
        source = work.source
        title = source.title if source else work.title
        description = source.description if source and source.description else ""
        updated += int(enrich_work(session, work, title, description))
    session.commit()
    return updated
