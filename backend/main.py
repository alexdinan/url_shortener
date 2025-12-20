from fastapi import FastAPI, status
from config import settings
from db import connect_to_db
import uvicorn

app = FastAPI()

# connect to DynamoDB using boto3.client
client = connect_to_db()

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    resp = client.list_tables()
    return {"Hello": resp}

# run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_CONTAINER_PORT)
