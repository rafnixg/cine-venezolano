import json
from types import SimpleNamespace

import pytest

from app.models import Work, YouTubeSource
from app.services import llm_catalog


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        metadata = {
            "title": "Una obra", "original_title": None, "synopsis": "Breve",
            "year": 2020, "country": "Venezuela", "language": "es", "subtitles": None,
            "content_type": "fiction", "length_category": "short", "genres": ["Drama"],
            "tags": ["Memoria"], "directors": [], "cast": [], "confidence": 0.8,
            "rationale": "Evidencia en la descripción",
        }
        return {
            "choices": [{"message": {"content": json.dumps(metadata)}}]
        }


class FakeClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.payload = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def post(self, _url, *, headers, json):
        self.payload = (headers, json)
        return FakeResponse()


def test_suggest_work_metadata_returns_cleaned_json(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(llm_catalog, "settings", SimpleNamespace(
        openrouter_api_key="test-key", openrouter_model="test/model", openrouter_timeout=10
    ))
    monkeypatch.setattr(llm_catalog.httpx, "Client", lambda **kwargs: client)
    work = Work(youtube_id="abc12345678", slug="una-obra", country="Venezuela")
    work.source = YouTubeSource(title="Una obra", description="Drama venezolano")

    result = llm_catalog.suggest_work_metadata(work)

    assert result["content_type"] == "fiction"
    assert result["confidence"] == 0.8
    assert client.payload[0]["Authorization"] == "Bearer test-key"
    assert client.payload[1]["response_format"]["type"] == "json_schema"


def test_suggest_work_metadata_requires_key(monkeypatch):
    monkeypatch.setattr(llm_catalog, "settings", SimpleNamespace(openrouter_api_key=""))
    with pytest.raises(llm_catalog.CatalogSuggestionError, match="OPENROUTER_API_KEY"):
        llm_catalog.suggest_work_metadata(Work(youtube_id="abc12345678", slug="obra"))
