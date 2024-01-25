import os
from tempfile import NamedTemporaryFile, gettempdir

import runpod
import requests

from aspect_ratio.conversion import (
    load_tased_model,
    device,
    compute_portrait_square_bboxes_with_scenes,
)


def download_video(url):
    response = requests.get(url, stream=True)
    if not response.ok:
        raise ValueError("Unable to download the video")

    # Create a temporary file
    with NamedTemporaryFile(delete=False, suffix=".mp4", dir=gettempdir()) as temp_file:
        # Write the video content to the temporary file
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)

        # Return the full path of the downloaded file
        return os.path.join(gettempdir(), temp_file.name)


model = load_tased_model(device)


def handler(job):
    """Handler function that will be used to process jobs."""
    job_input = job["input"]

    video_url = job_input.get("video_url")
    if not video_url:
        raise ValueError("video_url is required")

    video_path = download_video(video_url)

    (
        _,
        portrait_scene_boxes,
        _,
        _,
    ) = compute_portrait_square_bboxes_with_scenes(video_path, model=model)

    portrait_bounding_boxes = [bbox._asdict() for bbox in portrait_scene_boxes]
    return portrait_bounding_boxes


runpod.serverless.start({"handler": handler})
