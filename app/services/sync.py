from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SyncRun, Work, YouTubeSource
from app.services.classifier import (
    classify_length,
    infer_content_type,
    infer_year,
    parse_iso_duration,
    slugify,
)
from app.services.taxonomy import enrich_work
from app.services.youtube import YouTubeClient, YouTubeItem, best_thumbnail


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _unique_slug(session: Session, title: str, video_id: str) -> str:
    candidate = f"{slugify(title)[:150]}-{video_id.lower()}"
    existing = session.scalar(select(Work.id).where(Work.slug == candidate))
    return candidate if not existing else f"obra-{video_id.lower()}"


def _upsert_item(session: Session, item: YouTubeItem, now: datetime) -> bool:
    work = session.scalar(select(Work).where(Work.youtube_id == item.video_id))
    is_new = work is None
    video = item.video or {}
    snippet = video.get("snippet", {})
    details = video.get("contentDetails", {})
    status = video.get("status", {})
    stats = video.get("statistics", {})
    title = snippet.get("title") or item.playlist_title
    description = snippet.get("description") or item.playlist_description
    runtime = parse_iso_duration(details.get("duration"))
    available = bool(video) and status.get("privacyStatus", "public") == "public"

    if is_new:
        work = Work(
            youtube_id=item.video_id,
            slug=_unique_slug(session, title, item.video_id),
            year=infer_year(title),
            content_type=infer_content_type(title, description),
            length_category=classify_length(runtime),
            runtime_seconds=runtime,
            is_published=available,
            needs_review=True,
        )
        session.add(work)
        session.flush()
    else:
        work.runtime_seconds = runtime
        if work.needs_review:
            work.length_category = classify_length(runtime)

    work.is_available = available
    work.is_in_playlist = True
    work.last_seen_at = now
    if work.source is None:
        work.source = YouTubeSource(work_id=work.id, title=title)

    source = work.source
    source.title = title
    source.description = description
    source.channel_id = snippet.get("channelId")
    source.channel_title = snippet.get("channelTitle")
    source.video_published_at = _parse_datetime(snippet.get("publishedAt"))
    source.playlist_added_at = _parse_datetime(item.playlist_added_at)
    source.playlist_position = item.position
    source.thumbnail_url = best_thumbnail(snippet, item.video_id)
    source.embeddable = bool(status.get("embeddable", True))
    source.privacy_status = status.get("privacyStatus")
    source.view_count = int(stats["viewCount"]) if stats.get("viewCount") else None
    source.fetched_at = now
    enrich_work(session, work, title, description)
    return is_new


def _purge_stale_source(source: YouTubeSource) -> None:
    source.title = source.work.title_override or source.work.youtube_id
    source.description = None
    source.channel_id = None
    source.channel_title = None
    source.video_published_at = None
    source.playlist_added_at = None
    source.playlist_position = None
    source.thumbnail_url = None
    source.view_count = None


def sync_playlist(
    session: Session, client: YouTubeClient, playlist_id: str, source: str = "manual"
) -> SyncRun:
    run = SyncRun(source=source)
    session.add(run)
    session.commit()
    try:
        items = client.fetch_playlist(playlist_id)
        if not items:
            raise RuntimeError("La playlist no devolvió elementos; no se aplicaron cambios")
        now = datetime.now(UTC)
        seen: set[str] = set()
        for item in items:
            seen.add(item.video_id)
            if _upsert_item(session, item, now):
                run.added += 1
            else:
                run.updated += 1

        current = session.scalars(select(Work).where(Work.is_in_playlist.is_(True))).all()
        for work in current:
            if work.youtube_id not in seen:
                work.is_in_playlist = False
                work.is_available = False
                work.is_published = False
                run.hidden += 1

        cutoff = now - timedelta(days=30)
        stale_sources = session.scalars(
            select(YouTubeSource)
            .join(Work)
            .where(Work.is_in_playlist.is_(False), YouTubeSource.fetched_at < cutoff)
        ).all()
        for stale in stale_sources:
            _purge_stale_source(stale)

        run.status = "success"
        run.finished_at = now
        session.commit()
    except Exception as exc:
        session.rollback()
        persisted_run = session.get(SyncRun, run.id)
        if persisted_run:
            persisted_run.status = "failed"
            persisted_run.error = str(exc)[:2000]
            persisted_run.finished_at = datetime.now(UTC)
            session.commit()
            run = persisted_run
        raise
    return run
