import os

import requests

import googleapiclient.discovery as googleapiclient
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow


# https://github.com/googleapis/google-api-python-client/blob/main/docs/start.md

# personal, dont use in prod
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

    response = requests.post(
        "https://oauth2.googleapis.com/token", data=data, timeout=30000
    )
    access_token = response.json().get("access_token")
    print(access_token)
    return access_token


client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
redirect_uri = "http://localhost:8000/oauth/callback"
scopes = [
    "https://www.googleapis.com/auth/youtube.upload",
]


def upload_video_to_youtube(
    access_token: str, title: str, description: str, tags: list[str], video_path: str
):
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Step 1: Create the video resource
    video_details = {
        "snippet": {"description": description, "title": title, "tags": tags},
        "status": {"privacyStatus": "public"},  # Or 'private' or 'unlisted'
    }

    response = requests.post(
        "https://youtube.googleapis.com/youtube/v3/videos",
        params={"part": "snippet,status", "key": API_KEY},
        headers=headers,
        json=video_details,
    )

    if response.status_code != 200:
        print("Error creating video resource:", response.json())
        return

    video_resource = response.json()

    # Step 2: Upload the video content
    video_id = video_resource["id"]
    headers["Content-Type"] = "video/*"

    with open(video_path, "rb") as video_file:
        response = requests.put(
            f"https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&videoId={video_id}",
            headers=headers,
            data=video_file,
        )

    if response.status_code != 200:
        print("Error uploading video:", response.json())
    else:
        print("Video uploaded successfully:", response.json())
