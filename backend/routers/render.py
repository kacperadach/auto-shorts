from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter, Request
from fastapi.responses import PlainTextResponse

from shared.slack_bot.slack import send_slack_message
from shared.db.models import get_db_context_manager, RenderedVideo

from cloudrun import call_cloudrun_upload


router = APIRouter()


@router.post("/v1/render-webhook")
async def render_webhook(request: Request):
    try:
        body = await request.json()

        custom_data = body.get("customData")
        status = body.get("type")
        print(f"Received webhook: {status}")
        print(f"Custom data: {custom_data}")

        if status == "success":
            url = body.get("outputUrl")
            print(f"Successful render! {url} - Custom Data: {custom_data}")
            send_slack_message(f"Successful render! {url} - Custom Data: {custom_data}")

            with get_db_context_manager() as db:
                rendered_video = RenderedVideo(
                    s3_url=url,
                    duration=custom_data["duration"],
                    run_id=custom_data["run_id"],
                    repurposer_id=custom_data["repurposer_id"],
                    channel_id=custom_data["channel_id"],
                    video_id=custom_data["video_id"],
                )
                db.add(rendered_video)
                db.commit()
                db.refresh(rendered_video)

            call_cloudrun_upload(custom_data["repurposer_id"], rendered_video.id, url)

        elif status == "error":
            errors = body.get("errors")
            print(f"Failed render! {errors} - Custom Data: {custom_data}")
            send_slack_message(f"Failed render! {errors} - Custom Data: {custom_data}")
        elif status == "timeout":
            print(f"Render timed out! - Custom Data: {custom_data}")
            send_slack_message(f"Render timed out! - Custom Data: {custom_data}")
        else:
            print(f"Unknown render webhook type! {body}")
            send_slack_message(f"Unknown render webhook type! {body}")
    except Exception as e:
        print(f"Error in render webhook: {e}")
        send_slack_message(f"Error in render webhook: {e}")
