import settings
from pydantic import BaseModel, HttpUrl, Field

class CreateShortening(BaseModel):
    long_url: HttpUrl = Field(
        ...,
        title="Long URL",
        description="URL to be shortened. Must be a valid HTTP or HTTPS URL, max length 2083 chars",
        example="https://www.google.com"
    )

    alias: str | None = Field(
        default=None,
        title="Custom Alias",
        description=f"""Optional alias for shortened url. Must contain only letters, numbers, hyphens, underscores. 
                    Min length: {settings.MIN_ALIAS_LENGTH}. Max length: {settings.MAX_ALIAS_LENGTH}""",
        pattern=settings.CUSTOM_ALIAS_REGEX,
        example="flights-to-chile"
    )

class ShortUrl(BaseModel):
    short_url: str = Field(
        ...,
        title="Shortened URL",
        pattern=settings.SHORT_URL_REGEX,
        example="https://alexurl.com/urls/flights-to-chile"
    )
