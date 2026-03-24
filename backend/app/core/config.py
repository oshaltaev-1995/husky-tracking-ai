from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Husky Tracking API"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "husky_tracking"
    POSTGRES_USER: str = "husky_user"
    POSTGRES_PASSWORD: str = "husky_password"

    DATABASE_URL: str = (
        "postgresql+psycopg://husky_user:husky_password@db:5432/husky_tracking"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()