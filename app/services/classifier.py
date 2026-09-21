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
    "short": "Cortometraje",
    "medium": "Mediometraje",
    "feature": "Largometraje",
    "unknown": "Duración desconocida",
}

GENRE_RULES = {
    "Drama": ("drama", "dramático", "dramatico"),
    "Comedia": ("comedia", "comedy", "humor", "sátira", "satira", "sketch"),
    "Terror": ("terror", "horror", "sobrenatural", "maldición", "maldicion", "fantasma"),
    "Acción": ("película de acción", "pelicula de accion", "action movie", "adrenalina"),
    "Crimen": ("crimen", "criminal", "delincuente", "secuestro", "narcotráfico", "narcotrafico"),
    "Romance": ("romance", "romántica", "romantica", "historia de amor"),
    "Ciencia ficción": ("ciencia ficción", "ciencia ficcion", "sci-fi", "distopía", "distopia"),
    "Experimental": ("experimental", "videoarte", "video arte", "ensayo audiovisual"),
    "Biográfico": (
        "biográfico",
        "biografico",
        "biopic",
        "basada en la vida",
        "based on a true story",
    ),
}

TAG_RULES = {
    "Caracas": ("caracas",),
    "Memoria": ("memoria", "recuerdos", "archivo familiar", "videos de archivo"),
    "Identidad": ("identidad", "pertenencia", "raíces", "raices"),
    "Migración": ("migración", "migracion", "migrante", "diáspora", "diaspora", "exilio"),
    "Música y baile": ("música", "musica", "baile", "danza", "raptor house", "tuki"),
    "Política": ("dictadura", "política", "politica", "protesta", "presidente", "revolución"),
    "Diversidad": ("queer", "lgbt", "transgénero", "transgenero", "homosexual"),
    "Infancia y juventud": ("infancia", "niño", "niña", "adolescente", "juventud"),
    "Deporte": ("boxeo", "boxeador", "fútbol", "futbol", "deporte", "atleta"),
    "Naturaleza": ("naturaleza", "el ávila", "el avila", "selva", "ecológico", "ecologico"),
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
    text = f"{title} {description[:700]}".lower()
    if any(word in text for word in ("documental", "documentary", "docu ")):
        return "documentary"
    if any(word in text for word in ("animación", "animacion", "animated", "stop motion")):
        return "animation"
    if any(word in text for word in ("capítulo", "capitulo", "episodio", "serie venezolana")):
        return "series_episode"
    if any(word in text for word in ("video oficial", "official music video", "videoclip")):
        return "music_video"
    if any(
        word in text
        for word in (
            "película",
            "pelicula",
            "cortometraje",
            "corto venezolano",
            "short film",
            "shortfilm",
            "full movie",
            "largometraje",
        )
    ):
        return "fiction"
    return "other"


def infer_genres(title: str, description: str = "") -> list[str]:
    text = f"{title} {description[:700]}".lower()
    return [name for name, terms in GENRE_RULES.items() if any(term in text for term in terms)]


def infer_tags(title: str, description: str = "") -> list[str]:
    text = f"{title} {description[:900]}".lower()
    return [name for name, terms in TAG_RULES.items() if any(term in text for term in terms)]


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
