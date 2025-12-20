from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    ENV: Literal["prod", "dev"] = "dev"
    AWS_REGION: str = "eu-west-2"
    DYNAMODB_HOSTNAME: str | None = None
    DYNAMODB_CONTAINER_PORT: int = 8000
    BACKEND_CONTAINER_PORT: int = 80

settings = Settings()
