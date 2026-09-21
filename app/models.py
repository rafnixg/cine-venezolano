from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


work_genres = Table(
    "work_genres",
    Base.metadata,
    Column("work_id", ForeignKey("works.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

work_tags = Table(
    "work_tags",
    Base.metadata,
    Column("work_id", ForeignKey("works.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Work(Base):
    __tablename__ = "works"

    id: Mapped[int] = mapped_column(primary_key=True)
    youtube_id: Mapped[str] = mapped_column(String(11), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    title_override: Mapped[str | None] = mapped_column(String(300))
    original_title: Mapped[str | None] = mapped_column(String(300))
    synopsis: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    country: Mapped[str] = mapped_column(String(80), default="Venezuela")
    language: Mapped[str | None] = mapped_column(String(120))
    subtitles: Mapped[str | None] = mapped_column(String(120))
    content_type: Mapped[str] = mapped_column(String(32), default="other", index=True)
    length_category: Mapped[str] = mapped_column(String(20), default="unknown", index=True)
    runtime_seconds: Mapped[int | None] = mapped_column(Integer)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_in_playlist: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    source: Mapped[YouTubeSource | None] = relationship(
        back_populates="work", cascade="all, delete-orphan", uselist=False
    )
    genres: Mapped[list[Genre]] = relationship(secondary=work_genres, back_populates="works")
    tags: Mapped[list[Tag]] = relationship(secondary=work_tags, back_populates="works")
    credits: Mapped[list[Credit]] = relationship(
        back_populates="work", cascade="all, delete-orphan", order_by="Credit.position"
    )

    @property
    def title(self) -> str:
        return self.title_override or (self.source.title if self.source else self.youtube_id)

    @property
    def thumbnail_url(self) -> str:
        if self.source and self.source.thumbnail_url:
            return self.source.thumbnail_url
        return f"https://i.ytimg.com/vi/{self.youtube_id}/hqdefault.jpg"


class YouTubeSource(Base):
    __tablename__ = "youtube_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    work_id: Mapped[int] = mapped_column(
        ForeignKey("works.id", ondelete="CASCADE"), unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    channel_id: Mapped[str | None] = mapped_column(String(64))
    channel_title: Mapped[str | None] = mapped_column(String(200))
    video_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    playlist_added_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    playlist_position: Mapped[int | None] = mapped_column(Integer)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    embeddable: Mapped[bool] = mapped_column(Boolean, default=True)
    privacy_status: Mapped[str | None] = mapped_column(String(30))
    view_count: Mapped[int | None] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    work: Mapped[Work] = relationship(back_populates="source")


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    works: Mapped[list[Work]] = relationship(secondary=work_genres, back_populates="genres")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    works: Mapped[list[Work]] = relationship(secondary=work_tags, back_populates="tags")


class Credit(Base):
    __tablename__ = "credits"
    __table_args__ = (UniqueConstraint("work_id", "role", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(160))
    position: Mapped[int] = mapped_column(Integer, default=0)
    work: Mapped[Work] = relationship(back_populates="credits")


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="running")
    source: Mapped[str] = mapped_column(String(30), default="scheduled")
    added: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    hidden: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
