from __future__ import annotations

from app.models import Work
from app.services.classifier import (
    CONTENT_LABELS,
    LENGTH_LABELS,
    format_runtime,
)

MONTHS_ES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def format_date_es(value) -> str | None:
    if not value:
        return None
    return f"{value.day} de {MONTHS_ES[value.month - 1]} de {value.year}"


def description_excerpt(value: str | None, limit: int = 700) -> str | None:
    if not value:
        return None
    paragraphs = [part.strip() for part in value.replace("\r", "").split("\n\n") if part.strip()]
    useful = next(
        (
            part
            for part in paragraphs
            if not part.lower().startswith(("http://", "https://", "síguenos", "siguenos"))
        ),
        None,
    )
    if not useful:
        return None
    return useful if len(useful) <= limit else f"{useful[: limit - 1].rstrip()}…"


def work_dict(work: Work, detailed: bool = False) -> dict[str, object]:
    data: dict[str, object] = {
        "id": work.id,
        "youtube_id": work.youtube_id,
        "slug": work.slug,
        "title": work.title,
        "year": work.year,
        "country": work.country,
        "content_type": work.content_type,
        "content_type_label": CONTENT_LABELS.get(work.content_type, "Otro"),
        "length_category": work.length_category,
        "length_label": LENGTH_LABELS.get(work.length_category, "Duración desconocida"),
        "runtime_seconds": work.runtime_seconds,
        "runtime_label": format_runtime(work.runtime_seconds),
        "thumbnail_url": work.thumbnail_url,
        "genres": [{"name": genre.name, "slug": genre.slug} for genre in work.genres],
        "tags": [{"name": tag.name, "slug": tag.slug} for tag in work.tags],
    }
    if detailed:
        source = work.source
        data.update(
            {
                "original_title": work.original_title,
                "synopsis": work.synopsis,
                "language": work.language,
                "subtitles": work.subtitles,
                "channel_title": source.channel_title if source else None,
                "channel_url": (
                    f"https://www.youtube.com/channel/{source.channel_id}"
                    if source and source.channel_id
                    else None
                ),
                "description": source.description if source else None,
                "description_excerpt": description_excerpt(source.description if source else None),
                "published_at": source.video_published_at if source else None,
                "published_label": format_date_es(source.video_published_at if source else None),
                "embeddable": source.embeddable if source else False,
                "youtube_url": f"https://www.youtube.com/watch?v={work.youtube_id}",
                "credits": [{"role": credit.role, "name": credit.name} for credit in work.credits],
            }
        )
    return data
