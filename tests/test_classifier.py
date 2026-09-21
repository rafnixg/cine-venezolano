from app.services.classifier import (
    classify_length,
    infer_content_type,
    infer_year,
    parse_iso_duration,
    slugify,
)


def test_slugify_handles_spanish_text() -> None:
    assert slugify("¿Quién Quiere Tuki?") == "quien-quiere-tuki"


def test_parse_youtube_duration() -> None:
    assert parse_iso_duration("PT1H25M34S") == 5134
    assert parse_iso_duration("PT5M21S") == 321
    assert parse_iso_duration(None) is None


def test_length_boundaries() -> None:
    assert classify_length(1799) == "short"
    assert classify_length(1800) == "medium"
    assert classify_length(3600) == "feature"
    assert classify_length(None) == "unknown"


def test_conservative_content_inference() -> None:
    assert infer_content_type("Ventanas - Documental") == "documentary"
    assert infer_content_type("Capítulo 1 - Serie Venezolana") == "series_episode"
    assert infer_content_type("De Mí (Video Oficial)") == "music_video"
    assert infer_content_type("Una película venezolana") == "fiction"
    assert infer_content_type("Guasare") == "other"


def test_year_inference() -> None:
    assert infer_year("Mimicora (2024)") == 2024
    assert infer_year("Sin fecha") is None
