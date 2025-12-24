from fastapi import FastAPI, status, HTTPException
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
                "expires_at": {"N": str(int(datetime.now().timestamp()) + settings.URL_EXPIRY_TIME)}
            },
            ConditionExpression="attribute_not_exists(short_code)"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # duplicate alias/short_code
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alias already in use")
        else:
            # internal DB error
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB Error")


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
                raise e
            
    # no unique url found - keyspace is too small
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to generate a unique short url"
    )


# run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.BACKEND_CONTAINER_PORT)
