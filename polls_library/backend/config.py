from typing import Literal
from pydantic import (
    PostgresDsn,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # DEBUG SETTINGS
    @computed_field  # type: ignore
    @property
    def DEBUG(self) -> bool:
        return True if self.ENVIRONMENT == "DEV" else False
    DEBUG_AUTHLIB_LOG: bool = True
    DEBUG_ECHO_SQL: bool = False
    DEBUG_REDIRECT_APIV1: bool = True
    DEBUG_USE_SQLITE: bool = True

    # BACKEND SETTINGS
    BACKEND_PAGINATION_AMOUNT: int = 100

    # DEPLOY SETTINGS
    HTTPS: bool = True
    API_V1_STR: str = "/api/v1"
    ALLOWED_HOSTS: list[str] = ['localhost','127.0.0.1','0.0.0.0']

    SECRET_KEY: str
    MAX_SESSION_AGE: int = 60 * 60 # 1 hour
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days
    ENVIRONMENT: Literal["DEV", "PROD"] = "DEV"

    BACKEND_HOST: str = 'localhost'
    BACKEND_PORT: int = 8080
    PROJECT_NAME: str

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_DISCOVERY_URL: str

    @computed_field  # type: ignore
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        if settings.DEBUG_USE_SQLITE:
            sqlite_file_name = "database.db"
            return f"sqlite+aiosqlite:///db/{sqlite_file_name}"
        else:
            return MultiHostUrl.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )



settings = Settings()  # type: ignore