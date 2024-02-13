import os

from fastapi import FastAPI
from pydantic import BaseModel

from script import run
from shared.upload import upload_video

app = FastAPI()


class AutoRepurposeRequest(BaseModel):
    run_id: str
    video_id: str
    channel_id: str
    is_manual: bool


@app.post("/run")
async def auto_repurpose(repurpose_request: AutoRepurposeRequest):
    print(f"Received request: {repurpose_request}")
    await run(
        repurpose_request.run_id,
        repurpose_request.video_id,
        repurpose_request.channel_id,
        repurpose_request.is_manual,
    )


class UploadRequest(BaseModel):
    repurposer_id: str
    rendered_video_id: str
    s3_url: str


@app.post("/upload")
async def upload_video_cloudrun(upload_request: UploadRequest):
    print(f"Received upload request: {upload_request}")
    upload_video(
        upload_request.s3_url,
        upload_request.repurposer_id,
        upload_request.rendered_video_id,
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))  # Default to 8080 if PORT not set
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
    )
