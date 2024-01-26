import os

from fastapi import FastAPI
from pydantic import BaseModel

from script import run

app = FastAPI()


class AutoRepurposeRequest(BaseModel):
    primary_youtube_url: str
    secondary_youtube_url: str
    topic: str


@app.post("/run")
async def auto_repurpose(repurpose_request: AutoRepurposeRequest):
    print(f"Received request: {repurpose_request}")
    await run(
        repurpose_request.primary_youtube_url,
        repurpose_request.secondary_youtube_url,
        repurpose_request.topic,
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))  # Default to 8080 if PORT not set
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
    )
