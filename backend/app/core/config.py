from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str
    GROQ_API_KEY: str
    UPLOAD_DIR: Path = Path("./uploads")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
