from __future__ import annotations

import re
import unicodedata

CONTENT_LABELS = {
    "fiction": "Ficción",
    "documentary": "Documental",
    "animation": "Animación",
    "series_episode": "Serie / episodio",
    "music_video": "Videoclip",
    "other": "Otro",
}

LENGTH_LABELS = {
    "short": "Corta duración",
    "medium": "Media duración",
    "feature": "Largometraje",
    "unknown": "Duración desconocida",
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "obra"


def classify_length(seconds: int | None) -> str:
    if seconds is None:
        return "unknown"
    if seconds < 30 * 60:
        return "short"
    if seconds < 60 * 60:
        return "medium"
    return "feature"


def infer_content_type(title: str, description: str = "") -> str:
    text = f"{title} {description}".lower()
    if any(word in text for word in ("documental", "documentary", "docu ")):
        return "documentary"
    if any(word in text for word in ("animación", "animacion", "animated", "stop motion")):
        return "animation"
    if any(word in text for word in ("capítulo", "capitulo", "episodio", "serie venezolana")):
        return "series_episode"
    if any(word in text for word in ("video oficial", "official music video", "videoclip")):
        return "music_video"
    if any(
        word in text for word in ("película", "pelicula", "cortometraje", "short film", "shortfilm")
    ):
        return "fiction"
    return "other"


def infer_year(title: str) -> int | None:
    years = re.findall(r"(?:19|20)\d{2}", title)
    if not years:
        return None
    year = int(years[-1])
    return year if 1896 <= year <= 2100 else None


def parse_iso_duration(value: str | None) -> int | None:
    if not value:
        return None
    match = re.fullmatch(r"P(?:([0-9]+)D)?T?(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+)S)?", value)
    if not match:
        return None
    days, hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def format_runtime(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    return f"{hours} h {minutes:02d} min" if hours else f"{minutes} min"
