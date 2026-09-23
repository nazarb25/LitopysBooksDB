from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LITOPYSDB_",
        extra="ignore",
    )

    database_path: Path = Path("data/litopys.db")
    pdf_directory: Path = Path("data/pdfs")
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    auto_migrate: bool = True
    database_snapshot_url: str = (
        "https://github.com/nazarb25/LitopysBooksDB/releases/latest/download/litopys.db.zst"
    )
