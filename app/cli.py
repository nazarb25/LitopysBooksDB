from alembic import command
from alembic.config import Config

from app.bootstrap.container import create_container
from app.infrastructure.config.settings import Settings
from app.presentation.cli.parser import create_parser
from app.presentation.cli.runner import run_command


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    settings = Settings()
    updates = {}
    if args.db is not None:
        updates["database_path"] = args.db
    if args.pdf_dir is not None:
        updates["pdf_directory"] = args.pdf_dir
    if updates:
        settings = settings.model_copy(update=updates)

    if args.command in {"db-upgrade", "serve", "sync"}:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", f"sqlite:///{settings.database_path}")
        command.upgrade(config, "head")
    if args.command == "db-upgrade":
        return

    container = create_container(settings)
    try:
        if args.command == "serve":
            import uvicorn

            from app.main import create_app

            uvicorn.run(
                create_app(container.search_books),
                host=args.host or settings.host,
                port=args.port or settings.port,
            )
        else:
            run_command(args, container)
    except ValueError as exc:
        parser.error(str(exc))
    finally:
        container.close()


if __name__ == "__main__":
    main()
