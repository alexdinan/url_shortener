from fastapi import FastAPI, status

app = FastAPI()

@app.get("/", status_code=status.HTTP_200_OK)
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
