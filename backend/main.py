from fastapi import FastAPI, status, HTTPException, Path
from typing import Annotated
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from string import ascii_letters
import uvicorn
import random
import db
import settings
import models

# initialise api
app = FastAPI()
# config object holds environment variables
config = settings.config

for route in app.routes:
    print(route.path, route.methods)


def write_item(alias: str, long_url: str) -> None:
    now_timestamp = str(int(datetime.now().timestamp()))
    try:
        # write item to db
        db.client.put_item(
            TableName="url_mappings",
            Item={
                "short_code": {"S": alias},
                "long_url": {"S": long_url},
                "expires_at": {"N": str(int(now_timestamp) + settings.URL_EXPIRY_TIME)},
                "created_at": {"N": now_timestamp},
                "last_accessed": {"N": now_timestamp},
                "num_clicks": {"N": "0"}
            },
            ConditionExpression="attribute_not_exists(short_code)"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # duplicate alias/short_code
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alias already in use")
        else:
            # internal DB error
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error")


def fetch_item(alias: str, projection: str | None = None) -> dict[str, dict]:
    kwargs = {"TableName": "url_mappings", "Key": {"short_code": {"S": alias}}}
    if projection is not None:
        kwargs["ProjectionExpression"] = projection
    
    try:
        item = db.client.get_item(**kwargs)
        print(item)
        item = item.get("Item", None)
        if item is None:
            # no short-url with alias exists
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")
        return item
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")


def update_item(alias: str) -> None:
    now_timestamp = int(datetime.now().timestamp())

    try:
        # update metrics values for item
        db.client.update_item(
            TableName="url_mappings",
            Key={"short_code": {"S": alias}},
            UpdateExpression="""
                SET 
                    last_accessed = :now,
                    num_clicks = if_not_exists(num_clicks, :zero) + :one,
                    expires_at = :ttl
            """,
            ExpressionAttributeValues={
                ":now": {"N": str(now_timestamp)},
                ":zero": {"N": "0"},
                ":one": {"N": "1"},
                ":ttl": {"N": str(now_timestamp + settings.URL_EXPIRY_TIME)}
            }
        )
    except ClientError as e:
        print(f"WARNING: analytics update failed for PK: {alias}.\nDetails:\n{e}")


def convert_time(unix_timestamp: int) -> str:
    # convert from unix timestamp to ISO 8601 time format
    dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


@app.post("/urls", response_model=models.ShortUrl, status_code=status.HTTP_201_CREATED)
def create_shortening(shortening: models.CreateShortening) -> models.ShortUrl:
    # extract url and alias from request body
    data = shortening.model_dump()
    long_url = str(data["long_url"])
    alias = data["alias"]

    # handle custom aliases
    if alias is not None:
        write_item(alias, long_url)
        return models.ShortUrl(short_url=f"{config.BASE_URL}/{alias}")
    
    # generate random alias, retry until unique
    for _ in range(settings.MAX_RETRIES):
        alias = "".join(random.choices(ascii_letters, k=settings.DEFAULT_ALIAS_LENGTH))

        try:
            write_item(alias, long_url)
            return models.ShortUrl(short_url=f"{config.BASE_URL}/{alias}")
        
        except HTTPException as e:
            if e.status_code != status.HTTP_409_CONFLICT:
                # raise internal DB errors
                raise
            
    # no unique url found - keyspace is too small
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to generate a unique short url"
    )


@app.get("/urls/{alias}", response_model=models.UrlMetrics, status_code=status.HTTP_200_OK)
def get_url_metrics(alias: Annotated[str, Path(description="Alias for short URL")]) -> models.UrlMetrics:
    item = fetch_item(alias)

    # extract metrics from db response data
    metrics = {}
    metrics["num_clicks"] = int(item["num_clicks"]["N"])
    metrics["long_url"] = item["long_url"]["S"]
    for attr in ["created_at", "last_accessed", "expires_at"]:
        metrics[attr] = convert_time(int(item[attr]["N"]))

    return models.UrlMetrics(**metrics)


@app.get("/{alias}", status_code=status.HTTP_302_FOUND)
def redirect(alias: Annotated[str, Path(description="Alias for short URL")]) -> None:
    long_url = fetch_item(alias, projection="long_url")["long_url"]["S"]
    # update expiry and analytics metrics
    update_item(alias)

    return RedirectResponse(
        url=long_url,
        status_code=status.HTTP_302_FOUND,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"
        }
    )


# run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.BACKEND_CONTAINER_PORT)
