from fastapi import FastAPI, status, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime
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


def write_shortening(alias: str, long_url: str) -> None:
    try:
        # write item to db
        db.client.put_item(
            TableName="url_mappings",
            Item={
                "short_code": {"S": alias},
                "long_url": {"S": long_url},
                "expires_at": {"N": str(int(datetime.now().timestamp()) + settings.URL_EXPIRY_TIME)},
                "created_at": {"N": str(int(datetime.now().timestamp()))},
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


def fetch_long_url(alias: str) -> str:
    try:
        # get long_url for short_code matching alias
        resp = db.client.get_item(
            TableName="url_mappings",
            Key={"short_code": {"S": alias}},
            ProjectionExpression="long_url"
        )
        
        item = resp.get("Item", None)
        if item is None:
            # no match found
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")
        return item["long_url"]["S"]

    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")


def update_item(alias: str) -> None:
    try:
        # increment num_clicks metric if attribute exists
        db.client.update_item(
            TableName="url_mappings",
            Key={"short_code": {"S": alias}},
            UpdateExpression="SET num_clicks = num_clicks + 1",
            ConditionExpression="attribute_exists(num_clicks)"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            print(f"WARNING: analytics update failed for PK: {alias}, ATTR: num_clicks")
    
    try:
        # extend expiry of link (ttl) if it has an expiry
        db.client.update_item(
            TableName="url_mappings",
            Key={"short_code": {"S": alias}},
            UpdateExpression="SET expires_at = expires_at + :inc",
            ExpressionAttributeValues={":inc": {"N": str(settings.URL_EXPIRY_TIME)}},
            ConditionExpression="attribute_exists(expires_at)"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            print(f"WARNING: analytics update failed for PK: {alias}, ATTR: expires_at")


@app.post("/urls", response_model=models.ShortUrl, status_code=status.HTTP_201_CREATED)
def create_shortening(shortening: models.CreateShortening) -> models.ShortUrl:
    # extract url and alias from request body
    data = shortening.model_dump()
    long_url = str(data["long_url"])
    alias = data["alias"]

    # handle custom aliases
    if alias is not None:
        write_shortening(alias, long_url)
        return models.ShortUrl(short_url=f"{config.BASE_URL}/{alias}")
    
    # generate random alias, retry until unique
    for _ in range(settings.MAX_RETRIES):
        alias = "".join(random.choices(ascii_letters, k=settings.DEFAULT_ALIAS_LENGTH))

        try:
            write_shortening(alias, long_url)
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


@app.get("/{alias}", status_code=status.HTTP_302_FOUND)
def redirect(alias: str) -> None:
    long_url = fetch_long_url(alias)
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
