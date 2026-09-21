from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/cine.db")
    youtube_playlist_id: str = os.getenv(
        "YOUTUBE_PLAYLIST_ID", "PLVQ42obHL2u_nJgblVTpWs3NQdD_WZkAM"
    )
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    admin_password_hash: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    session_secret: str = os.getenv("SESSION_SECRET", "development-only-change-me")
    session_https_only: bool = _as_bool(os.getenv("SESSION_HTTPS_ONLY"), False)
    sync_timezone: str = os.getenv("SYNC_TIMEZONE", "America/Caracas")
    sync_day_of_week: str = os.getenv("SYNC_DAY_OF_WEEK", "sun")
    sync_hour: int = int(os.getenv("SYNC_HOUR", "3"))


settings = Settings()
