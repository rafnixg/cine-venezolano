from __future__ import annotations

import argparse
import getpass

from argon2 import PasswordHasher

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.sync import sync_playlist
from app.services.youtube import YouTubeClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Administración del catálogo")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-db", help="Crea las tablas de la base de datos")
    subparsers.add_parser("sync-youtube", help="Sincroniza la playlist configurada")
    password_parser = subparsers.add_parser("hash-password", help="Genera un hash Argon2")
    password_parser.add_argument("password", nargs="?", help="Omítela para ingresarla en privado")
    args = parser.parse_args()

    if args.command == "init-db":
        Base.metadata.create_all(engine)
        print("Base de datos inicializada.")
    elif args.command == "hash-password":
        password = args.password or getpass.getpass("Contraseña: ")
        if len(password) < 12:
            parser.error("La contraseña debe tener al menos 12 caracteres")
        print(PasswordHasher().hash(password))
    elif args.command == "sync-youtube":
        Base.metadata.create_all(engine)
        client = YouTubeClient(settings.youtube_api_key)
        try:
            with SessionLocal() as session:
                run = sync_playlist(session, client, settings.youtube_playlist_id, source="cli")
                print(
                    f"Sincronización completa: {run.added} altas, "
                    f"{run.updated} actualizaciones, {run.hidden} ocultas."
                )
        finally:
            client.close()


if __name__ == "__main__":
    main()
