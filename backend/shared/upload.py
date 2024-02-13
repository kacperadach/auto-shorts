import os
from uuid import uuid4

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import requests
from sqlalchemy.orm import Session, joinedload

from shared.slack_bot.slack import send_slack_message
from shared.db.models import (
    Repurposer,
    get_db_context_manager,
    RepurposerSocialMediaAccount,
    SocialMediaAccount,
    RenderedVideo,
)

client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
API_KEY = os.getenv("GOOGLE_API_KEY")


def get_access_token_for_youtube(refresh_token: str):
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    response = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=30000)
    access_token = response.json().get("access_token")
    return access_token


def get_youtube_client(access_token: str):
    return build("youtube", "v3", credentials=Credentials(token=access_token))


def get_video_metadata(repurposer: Repurposer):
    return {
        "snippet": {
            "title": repurposer.video_title,
            "description": repurposer.video_description,
            "tags": repurposer.video_tags,
            "categoryId": "22",  # Refer to YouTube's category list
        },
        "status": {"privacyStatus": "public"},  # or 'private' or 'unlisted'
    }


def download_video_from_url(url, destination_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(destination_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        return True
    return False


def _upload_video(youtube, video_url, body):
    random_id = str(uuid4())
    temp_video_path = f"/tmp/{random_id}.mp4"  # Temporary path to store downloaded video

    if not download_video_from_url(video_url, temp_video_path):
        print("Failed to download video.")
        return None

    try:
        # with open(temp_video_path, "rb") as file:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=MediaFileUpload(temp_video_path, chunksize=-1, resumable=True),
        )
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print("Uploaded %d%%." % int(status.progress() * 100))

        print(f"Final YouTube response {response}")  # TODO: get public youtube URL
        return response
    except Exception as e:
        print(f"Error uploading video: {e}")
        return None
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)


def upload_video(url: str, repurposer_id: str, rendered_video_id: str):
    with get_db_context_manager() as db:
        repurposer = (
            db.query(Repurposer)
            .filter(Repurposer.id == repurposer_id)
            .outerjoin(
                RepurposerSocialMediaAccount,
                Repurposer.id == RepurposerSocialMediaAccount.repurposer_id,
            )
            .options(joinedload(Repurposer.social_media_accounts))
            .one_or_none()
        )
        if not repurposer:
            return None

    for social_media_account in repurposer.social_media_accounts:
        if social_media_account.platform != "youtube":
            print("Only YouTube accounts are supported")
            continue

        access_token = get_access_token_for_youtube(social_media_account.refresh_token)
        if not access_token:
            send_slack_message(
                f"Failed to get access token for social media account: {social_media_account.title}"
            )
            print(
                f"Failed to get access token for social media account: {social_media_account.title}"
            )
            continue

        youtube = get_youtube_client(access_token)
        metadata = get_video_metadata(repurposer)

        success = _upload_video(youtube, url, metadata)
        if not success:
            send_slack_message(
                f"Failed to upload video for social media account: {social_media_account.title}, {url}"
            )
            print(
                f"Failed to upload video for social media account: {social_media_account.title}, {url}"
            )
            continue

        send_slack_message(
            f"Video uploaded for social media account: {social_media_account.title}: {success}"
        )
        print(
            f"Video uploaded for social media account: {social_media_account.title}: {success}"
        )

        with get_db_context_manager() as db:
            rendered_video = (
                db.query(RenderedVideo)
                .filter(RenderedVideo.id == rendered_video_id)
                .one_or_none()
            )
            if not rendered_video:
                print(f"Rendered video not found: {rendered_video_id}")
                continue

            rendered_video.youtube_video_id = success.get("id")
            db.commit()
