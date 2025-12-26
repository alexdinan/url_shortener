from pydantic_settings import BaseSettings
from typing import Literal

# app configuration
class Config(BaseSettings):
    ENV: Literal["prod", "dev"] = "dev"
    AWS_REGION: str = "eu-west-2"
    DYNAMODB_HOSTNAME: str | None = None
    DYNAMODB_CONTAINER_PORT: int = 8000
    BACKEND_CONTAINER_PORT: int = 80
    BASE_URL: str = "http://localhost:8080"

config = Config()

# app constants
MIN_ALIAS_LENGTH = 1
MAX_ALIAS_LENGTH = 100
DEFAULT_ALIAS_LENGTH = 8
URL_EXPIRY_TIME = 60 * 60 * 24 * 365
CUSTOM_ALIAS_REGEX = f"^[a-zA-Z0-9_-]{{{MIN_ALIAS_LENGTH},{MAX_ALIAS_LENGTH}}}$"
SHORT_URL_REGEX = f"{config.BASE_URL}/[a-zA-Z0-9_-]{{{MIN_ALIAS_LENGTH},{MAX_ALIAS_LENGTH}}}"
ISO_8601_REGEX = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
MAX_RETRIES = 10    # for generating a unique short_url
