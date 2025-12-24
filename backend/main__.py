from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from settings import *
from db import connect_to_db
import uvicorn
from botocore.exceptions import ClientError
from string import ascii_letters
from random import choices


# initialise api
app = FastAPI()

# connect to DynamoDB using boto3.client
client = connect_to_db()

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    resp = client.list_tables()
    return {"Hello": resp}


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
                    Min length: {MIN_ALIAS_LENGTH}. Max length: {MAX_ALIAS_LENGTH}""",
        pattern=CUSTOM_ALIAS_REGEX,
        example="flights-to-chile"
    )

class ShortUrl(BaseModel):
    short_url: str = Field(
        ...,
        title="Shortened URL",
        pattern=SHORT_URL_REGEX,
        example="https://alexurl.com/urls/flights-to-chile"
    )

# should return full shortened url. need domain name for this + create response model
@app.post("/urls", response_model=ShortUrl, status_code=status.HTTP_201_CREATED)
async def create_shortening(shortening: CreateShortening) -> ShortUrl:
    new_shortening = shortening.model_dump()

    if new_shortening["alias"] is not None:
        try:
            client.put_item(
                TableName="url_mappings",
                Item={
                    "short_code": {"S": new_shortening["alias"]},
                    "long_url": {"S": str(new_shortening["long_url"])},
                    "expires_at": {"N": str(int(datetime.now().timestamp()) + URL_EXPIRY_TIME)}
                },
                ConditionExpression="attribute_not_exists(short_code)"
            )
            return ShortUrl(short_url=f"{config.BASE_URL}/{new_shortening['alias']}")
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                # alias already exists
                raise HTTPException(status_code=409, detail="Alias already in use")
            else:
                # unexpected boto3 DB failure
                raise HTTPException(status_code=500, detail=f"Database Error")
    
    else:
        while True:
            # generate random fixed-length alias
            alias = "".join(choices(ascii_letters, k=DEFAULT_ALIAS_LENGTH))

            try:
                client.put_item(
                    TableName="url_mappings",
                    Item={
                        "short_code": {"S": alias},
                        "long_url": {"S": str(new_shortening["long_url"])},
                        "expires_at": {"N": str(int(datetime.now().timestamp()) + URL_EXPIRY_TIME)}
                    },
                    ConditionExpression="attribute_not_exists(short_code)"
                )
                return ShortUrl(short_url=f"{config.BASE_URL}/{new_shortening['alias']}")
                
            except ClientError as e:
                if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                    # unexpected boto3 DB failure
                    raise HTTPException(status_code=500, detail=f"Database Error")


        

    


# run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.BACKEND_CONTAINER_PORT)




# need to generate random short codes of given length
# need to retry until non-duplicate found
