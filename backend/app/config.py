from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI受発注プラットフォーム"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/orderring"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    REDIS_URL: str = "redis://redis:6379/0"

    ENCRYPTION_KEY: str = ""

    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
