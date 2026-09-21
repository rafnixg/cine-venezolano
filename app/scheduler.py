from __future__ import annotations

import logging
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.services.sync import sync_playlist
from app.services.youtube import YouTubeClient

logger = logging.getLogger(__name__)
scheduler: BackgroundScheduler | None = None
sync_lock = Lock()


def run_configured_sync(source: str) -> bool:
    if not settings.youtube_api_key:
        logger.info("Sincronización omitida: YOUTUBE_API_KEY no configurada")
        return False
    if not sync_lock.acquire(blocking=False):
        logger.info("Sincronización omitida: ya existe una ejecución activa")
        return False
    try:
        client = YouTubeClient(settings.youtube_api_key)
        try:
            with SessionLocal() as session:
                sync_playlist(session, client, settings.youtube_playlist_id, source=source)
        finally:
            client.close()
    except Exception:
        logger.exception("Falló la sincronización de YouTube")
        return False
    finally:
        sync_lock.release()
    return True


def scheduled_sync() -> None:
    run_configured_sync("scheduled")


def start_scheduler() -> BackgroundScheduler:
    global scheduler
    scheduler = BackgroundScheduler(timezone=settings.sync_timezone)
    scheduler.add_job(
        scheduled_sync,
        CronTrigger(
            day_of_week=settings.sync_day_of_week,
            hour=settings.sync_hour,
            minute=0,
            timezone=settings.sync_timezone,
        ),
        id="youtube-weekly-sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    return scheduler


def stop_scheduler() -> None:
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
    scheduler = None
