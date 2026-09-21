"""Initial catalog schema."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "works",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("youtube_id", sa.String(11), nullable=False),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("title_override", sa.String(300)),
        sa.Column("original_title", sa.String(300)),
        sa.Column("synopsis", sa.Text()),
        sa.Column("year", sa.Integer()),
        sa.Column("country", sa.String(80), nullable=False),
        sa.Column("language", sa.String(120)),
        sa.Column("subtitles", sa.String(120)),
        sa.Column("content_type", sa.String(32), nullable=False),
        sa.Column("length_category", sa.String(20), nullable=False),
        sa.Column("runtime_seconds", sa.Integer()),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("is_in_playlist", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("youtube_id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_works_youtube_id", "works", ["youtube_id"])
    op.create_index("ix_works_slug", "works", ["slug"])
    op.create_index("ix_works_content_type", "works", ["content_type"])
    op.create_index("ix_works_length_category", "works", ["length_category"])
    op.create_index("ix_works_year", "works", ["year"])
    op.create_index("ix_works_is_published", "works", ["is_published"])
    op.create_index("ix_works_needs_review", "works", ["needs_review"])
    op.create_index("ix_works_is_available", "works", ["is_available"])
    op.create_index("ix_works_is_in_playlist", "works", ["is_in_playlist"])
    op.create_table(
        "youtube_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "work_id",
            sa.Integer(),
            sa.ForeignKey("works.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("channel_id", sa.String(64)),
        sa.Column("channel_title", sa.String(200)),
        sa.Column("video_published_at", sa.DateTime(timezone=True)),
        sa.Column("playlist_added_at", sa.DateTime(timezone=True)),
        sa.Column("playlist_position", sa.Integer()),
        sa.Column("thumbnail_url", sa.Text()),
        sa.Column("embeddable", sa.Boolean(), nullable=False),
        sa.Column("privacy_status", sa.String(30)),
        sa.Column("view_count", sa.Integer()),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_youtube_sources_work_id", "youtube_sources", ["work_id"])
    for table in ("genres", "tags"):
        op.create_table(
            table,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(80), nullable=False, unique=True),
            sa.Column("slug", sa.String(80), nullable=False, unique=True),
        )
        op.create_index(f"ix_{table}_slug", table, ["slug"])
    op.create_table(
        "work_genres",
        sa.Column(
            "work_id", sa.Integer(), sa.ForeignKey("works.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "genre_id",
            sa.Integer(),
            sa.ForeignKey("genres.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "work_tags",
        sa.Column(
            "work_id", sa.Integer(), sa.ForeignKey("works.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
        ),
    )
    op.create_table(
        "credits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "work_id", sa.Integer(), sa.ForeignKey("works.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("work_id", "role", "name"),
    )
    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("added", sa.Integer(), nullable=False),
        sa.Column("updated", sa.Integer(), nullable=False),
        sa.Column("hidden", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text()),
    )


def downgrade() -> None:
    for table in (
        "sync_runs",
        "credits",
        "work_tags",
        "work_genres",
        "tags",
        "genres",
        "youtube_sources",
        "works",
    ):
        op.drop_table(table)
