import os
from time import sleep

from remotion_lambda import RenderMediaParams, Privacy, ValidStillImageFormats
from remotion_lambda import RemotionClient


# Load env variables
REMOTION_APP_REGION = os.getenv("REMOTION_APP_REGION")
if not REMOTION_APP_REGION:
    raise Exception("REMOTION_APP_REGION is not set")
REMOTION_APP_FUNCTION_NAME = os.getenv("REMOTION_APP_FUNCTION_NAME")
if not REMOTION_APP_FUNCTION_NAME:
    raise Exception("REMOTION_APP_FUNCTION_NAME is not set")
REMOTION_APP_SERVE_URL = os.getenv("REMOTION_APP_SERVE_URL")
if not REMOTION_APP_SERVE_URL:
    raise Exception("REMOTION_APP_SERVE_URL is not set")
# Construct client
client = RemotionClient(
    region=REMOTION_APP_REGION,
    serve_url=REMOTION_APP_SERVE_URL,
    function_name=REMOTION_APP_FUNCTION_NAME,
)


# primaryUrl: string;
# secondaryUrl: string;
# durationInSeconds: number;
# width: number;
# height: number;
# highlightColor: string;
# secondaryColor: string;
# segments: SubtitleSegment[];
# croppingBoxes: CroppingBox[];
# highlightColor="#33FF52"
# secondaryColor="#FF3352"


class RenderException(Exception):
    pass


def render_short(
    primary_url: str,
    secondary_url: str,
    durationInSeconds: int,
    segments: list,
    cropping_boxes: list,
    width: int = 1080,
    height: int = 1920,
    highlight_color: str = "#33FF52",
    secondary_color: str = "#FF3352",
):
    render_params = RenderMediaParams(
        composition="VideoComposition",
        privacy=Privacy.PUBLIC,
        input_props={
            "primaryUrl": primary_url,
            "secondaryUrl": secondary_url,
            "durationInSeconds": durationInSeconds,
            "width": width,
            "height": height,
            "highlightColor": highlight_color,
            "secondaryColor": secondary_color,
            "segments": segments,
            "croppingBoxes": cropping_boxes,
        },
    )
    render_response = client.render_media_on_lambda(render_params)
    if not render_response:
        raise RenderException("Failed to call render_media_on_lambda successfully")

    # Execute render request
    print("Render ID:", render_response.render_id)
    print("Bucket name:", render_response.bucket_name)
    # Execute progress request
    progress_response = client.get_render_progress(
        render_id=render_response.render_id, bucket_name=render_response.bucket_name
    )
    while progress_response and not progress_response.done:
        sleep(15)
        print("Overall progress")
        print(str(progress_response.overallProgress * 100) + "%")
        print(progress_response)
        progress_response = client.get_render_progress(
            render_id=render_response.render_id,
            bucket_name=render_response.bucket_name,
        )
    print("Render done!", progress_response.outputFile)
    return progress_response.outputFile
