from settings import config
import boto3
from mypy_boto3_dynamodb import DynamoDBClient

def connect_to_db() -> DynamoDBClient:
    kwargs = {"region_name": config.AWS_REGION}

    if config.ENV == "dev":
        if config.DYNAMODB_HOSTNAME is None:
            raise ValueError("DYNAMODB_HOSTNAME is required in dev mode")
        
        # connect to local DynamoDB container
        kwargs.update({
            "endpoint_url": f"http://{config.DYNAMODB_HOSTNAME}:{config.DYNAMODB_CONTAINER_PORT}",
            "aws_access_key_id": "dummy",
            "aws_secret_access_key": "dummy"
        })
    
    return boto3.client("dynamodb", **kwargs)

client = connect_to_db()
