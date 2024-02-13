import os
import urllib.parse
import json

from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter
import requests
from pydantic import BaseModel

# from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
# from fastapi.openapi.models import OAuthFlowAuthorizationCode
# from fastapi.openapi.models import OAuthFlowsAuthorizationCode
# from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from fastapi.openapi.models import OAuth2PasswordBearer as OAuth2PasswordBearerModel
# from fastapi.openapi.models import (
#     OAuth2PasswordRequestForm as OAuth2PasswordRequestFormModel,
# )
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

from auth.auth import ValidUserFromJWT
from shared.db.models import get_db_context_manager, SocialMediaAccount, User
from shared.s3.s3 import upload_file_obj_to_s3, download_image

router = APIRouter()

# OAuth 2.0 configuration
client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
redirect_uri = "https://api.autorepurpose.com/v1/oauth/callback"
scopes = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

instagram_client_id = os.getenv("INSTAGRAM_APP_ID")
instagram_client_secret = os.getenv("INSTAGRAM_APP_SECRET")

facebook_redirect_uri = "http://localhost:8000/facebook/oauth/callback"
facebook_scopes = ["user_profile"]


# Endpoint to initiate the OAuth 2.0 flow
@router.get("/v1/oauth/login")
async def initiate_oauth(
    user: User = Depends(ValidUserFromJWT()),
):
    user_metadata = {
        "user_id": user.id,
    }
    state = urllib.parse.quote_plus(json.dumps(user_metadata))

    flow = InstalledAppFlow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            },
        },
        scopes=scopes,
    )
    flow.redirect_uri = redirect_uri
    auth_url, _ = flow.authorization_url(prompt="consent", state=state)
    return {"auth_url": auth_url}


# def get_youtube_client(access_token: str):
#     credentials = Credentials(token=access_token)
#     return build("youtube", "v3", credentials=credentials)


# def get_video_metadata():
#     return {
#         "snippet": {
#             "title": "Your Video Title",
#             "description": "Description of your video",
#             "tags": ["sample", "video", "tags"],
#             "categoryId": "22",  # Refer to YouTube's category list
#         },
#         "status": {"privacyStatus": "public"},  # or 'private' or 'unlisted'
#     }


# def download_video_from_url(url, destination_path):
#     response = requests.get(url, stream=True)
#     if response.status_code == 200:
#         with open(destination_path, "wb") as file:
#             for chunk in response.iter_content(chunk_size=1024):
#                 file.write(chunk)
#         return True
#     return False


# def upload_video(youtube, video_url, body):
#     temp_video_path = "/tmp/temp_video.mp4"  # Temporary path to store downloaded video

#     # Download the video from the URL
#     if not download_video_from_url(video_url, temp_video_path):
#         print("Failed to download video.")
#         return None

#     try:
#         # Upload the downloaded video
#         with open(temp_video_path, "rb") as file:
#             request = youtube.videos().insert(
#                 part="snippet,status",
#                 body=body,
#                 media_body=MediaFileUpload(temp_video_path, chunksize=-1, resumable=True),
#             )
#             response = None
#             while response is None:
#                 status, response = request.next_chunk()
#                 if status:
#                     print("Uploaded %d%%." % int(status.progress() * 100))
#             return response
#     finally:
#         # Clean up: Delete the temporary video file
#         if os.path.exists(temp_video_path):
#             os.remove(temp_video_path)


def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", headers=headers
    )
    user_info = response.json()

    if "items" not in user_info or len(user_info["items"]) == 0:
        raise HTTPException(status_code=400, detail="Failed to get user info")

    item = user_info["items"][0]

    channel_id = item["id"]
    title = item["snippet"]["title"]
    thumbnail_url = item["snippet"]["thumbnails"]["default"]["url"]

    return {
        "channel_id": channel_id,
        "title": title,
        "thumbnail_url": thumbnail_url,
    }


# Endpoint to handle the OAuth callback
@router.get("/v1/oauth/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(...)):
    try:
        flow = InstalledAppFlow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                },
            },
            scopes=scopes,
        )
        flow.redirect_uri = redirect_uri
        flow.fetch_token(code=code)
        credentials = flow.credentials
        access_token = credentials.token
        refresh_token = credentials.refresh_token

        decoded_state = json.loads(urllib.parse.unquote_plus(state))
        user_id = decoded_state.get("user_id")

        channel_info = get_user_info(access_token)

        image = download_image(channel_info["thumbnail_url"])
        thumbnail_s3_url = await upload_file_obj_to_s3(
            image, f"thumbnails/channels/{channel_info['channel_id']}.jpg"
        )

        with get_db_context_manager() as db:
            db.add(
                SocialMediaAccount(
                    user_id=user_id,
                    platform="youtube",
                    refresh_token=refresh_token,
                    channel_id=channel_info["channel_id"],
                    title=channel_info["title"],
                    thumbnail_url=thumbnail_s3_url,
                )
            )
            db.commit()

        return "Success! You can now close this window."
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")


@router.get("/facebook/oauth/login")
async def facebook_initiate_oauth():
    flow = InstalledAppFlow.from_client_config(
        {
            "web": {
                "client_id": instagram_client_id,
                "client_secret": instagram_client_secret,
                "redirect_uris": [facebook_redirect_uri],
                "auth_uri": "https://api.instagram.com/oauth/authorize",
                "token_uri": "https://api.instagram.com/oauth/access_token",
            },
        },
        # scopes=[]
        scopes=facebook_scopes,
    )
    flow.redirect_uri = facebook_redirect_uri
    auth_url, _ = flow.authorization_url(prompt="consent")
    return {"auth_url": auth_url}


# Endpoint to handle the OAuth callback
@router.get("/facebook/oauth/callback")
async def facebook_oauth_callback(
    code: str = Query(...),
):
    try:
        flow = InstalledAppFlow.from_client_config(
            {
                "web": {
                    "client_id": instagram_client_id,
                    "client_secret": instagram_client_secret,
                    "redirect_uris": [facebook_redirect_uri],
                    "auth_uri": "https://api.instagram.com/oauth/authorize",
                    "token_uri": "https://api.instagram.com/oauth/access_token",
                },
            },
            scopes=facebook_scopes,
        )
        flow.redirect_uri = facebook_redirect_uri
        flow.fetch_token(code=code)
        credentials = flow.credentials
        access_token = credentials.token
        refresh_token = credentials.refresh_token

        # You can store the tokens securely or use them for API requests here
        # For example, you can return them as a JSON response to your frontend
        print(access_token)
        print(refresh_token)
        return {"access_token": access_token, "refresh_token": refresh_token}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
