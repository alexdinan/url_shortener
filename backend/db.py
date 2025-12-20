from config import settings
import boto3

def connect_to_db():
    kwargs = {"region_name": settings.AWS_REGION}

    if settings.ENV == "dev":
        if settings.DYNAMODB_HOSTNAME is None:
            raise ValueError("DYNAMODB_HOSTNAME is required in dev mode")
        
        # connect to local DynamoDB container
        kwargs.update({
            "endpoint_url": f"http://{settings.DYNAMODB_HOSTNAME}:{settings.DYNAMODB_CONTAINER_PORT}",
            "aws_access_key_id": "dummy",
            "aws_secret_access_key": "dummy"
        })
    
    return boto3.client("dynamodb", **kwargs)
