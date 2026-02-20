from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB + queue
    database_url: str = "postgresql+asyncpg://app:app@localhost:5433/docproc"
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    # AWS
    aws_region: str = "eu-west-2"
    aws_textract_s3_bucket: str = "textract-demo-bucket-wamiri"


settings = Settings()
