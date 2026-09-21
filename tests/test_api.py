from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Work, YouTubeSource

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)


def override_db():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        work = Work(
            youtube_id="abc12345678",
            slug="obra-prueba-abc12345678",
            title_override="Obra de prueba",
            content_type="fiction",
            length_category="short",
            runtime_seconds=600,
            is_published=True,
            is_available=True,
            is_in_playlist=True,
            needs_review=False,
        )
        work.source = YouTubeSource(
            title="Título en YouTube",
            description="Una historia venezolana de prueba.\n\nhttps://example.test",
            embeddable=True,
            playlist_position=0,
        )
        session.add(work)
        session.commit()


def test_health() -> None:
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_catalog_and_detail() -> None:
    response = client.get("/api/v1/works?q=prueba")
    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1
    slug = response.json()["items"][0]["slug"]
    detail = client.get(f"/api/v1/works/{slug}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Obra de prueba"

    homepage = client.get("/")
    assert homepage.status_code == 200
    assert "Daniela Carrión" in homepage.text
    assert "PLVQ42obHL2u_nJgblVTpWs3NQdD_WZkAM" in homepage.text
    assert "AGPL-3.0-or-later" in homepage.text
    html = client.get(f"/obras/{slug}")
    assert html.status_code == 200
    assert "Obra de prueba" in html.text
    assert "Ficha técnica" in html.text
    assert "Una historia venezolana de prueba." in html.text


def test_admin_login_page_renders() -> None:
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "Administración" in response.text
    assert 'name="password"' in response.text


def test_hidden_work_is_not_public() -> None:
    with Session(engine) as session:
        work = session.query(Work).first()
        work.is_published = False
        session.commit()
    assert client.get("/api/v1/works").json()["pagination"]["total"] == 0
    assert client.get("/api/v1/works/obra-prueba-abc12345678").status_code == 404


def test_empty_filters_are_accepted_and_pagination_urls_are_clean() -> None:
    with Session(engine) as session:
        for index in range(1, 25):
            work = Work(
                youtube_id=f"vid{index:08d}",
                slug=f"obra-{index}",
                title_override=f"Obra {index}",
                content_type="fiction",
                length_category="short",
                runtime_seconds=600,
                is_published=True,
                is_available=True,
                is_in_playlist=True,
            )
            work.source = YouTubeSource(title=f"Obra {index}", playlist_position=index)
            session.add(work)
        session.commit()

    url = "/?q=&type=&length=&genre=&year=&sort=playlist"
    response = client.get(url)
    assert response.status_code == 200
    assert "year=" not in response.text
    assert "page=2" in response.text
    assert client.get(f"{url}&page=2").status_code == 200
    assert client.get("/api/v1/works?year=").status_code == 200


def test_invalid_year_has_clear_validation_error() -> None:
    response = client.get("/?year=no-es-un-año")
    assert response.status_code == 422
    assert response.json()["detail"] == "El año debe ser un número entero"
