from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Work
from app.services.sync import sync_playlist
from app.services.youtube import YouTubeItem


class FakeYouTubeClient:
    def __init__(self, items):
        self.items = items

    def fetch_playlist(self, _playlist_id):
        return self.items


def item(video_id="abc12345678", title="Corto venezolano (2024)"):
    return YouTubeItem(
        video_id=video_id,
        position=0,
        playlist_added_at="2025-01-02T00:00:00Z",
        playlist_title=title,
        playlist_description="Un cortometraje de drama.",
        video={
            "id": video_id,
            "snippet": {
                "title": title,
                "description": "Un cortometraje de drama.",
                "channelId": "channel",
                "channelTitle": "Canal",
                "publishedAt": "2024-03-01T00:00:00Z",
                "thumbnails": {"high": {"url": "https://example.test/image.jpg"}},
            },
            "contentDetails": {"duration": "PT12M10S"},
            "status": {"privacyStatus": "public", "embeddable": True},
            "statistics": {"viewCount": "42"},
        },
    )


def make_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_sync_creates_and_updates_without_overwriting_editorial_data() -> None:
    with make_session() as session:
        first = sync_playlist(session, FakeYouTubeClient([item()]), "playlist")
        assert first.added == 1
        work = session.scalar(select(Work))
        assert work.title == "Corto venezolano (2024)"
        assert work.year == 2024
        assert work.length_category == "short"
        work.title_override = "Título curado"
        work.needs_review = False
        session.commit()

        second = sync_playlist(
            session, FakeYouTubeClient([item(title="Título modificado en YouTube")]), "playlist"
        )
        session.refresh(work)
        assert second.updated == 1
        assert work.title == "Título curado"
        assert work.source.title == "Título modificado en YouTube"


def test_missing_item_is_hidden_not_deleted() -> None:
    with make_session() as session:
        sync_playlist(session, FakeYouTubeClient([item()]), "playlist")
        second_item = item("zyx12345678", "Otra película")
        run = sync_playlist(session, FakeYouTubeClient([second_item]), "playlist")
        old = session.scalar(select(Work).where(Work.youtube_id == "abc12345678"))
        assert run.hidden == 1
        assert old is not None
        assert not old.is_published
        assert not old.is_in_playlist
