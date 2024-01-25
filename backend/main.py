from dotenv import load_dotenv

load_dotenv()

import os

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
# from fastapi.openapi.models import OAuthFlowAuthorizationCode
# from fastapi.openapi.models import OAuthFlowsAuthorizationCode
# from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from fastapi.openapi.models import OAuth2PasswordBearer as OAuth2PasswordBearerModel
# from fastapi.openapi.models import (
#     OAuth2PasswordRequestForm as OAuth2PasswordRequestFormModel,
# )
from google_auth_oauthlib.flow import InstalledAppFlow


app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# OAuth 2.0 configuration
client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
redirect_uri = "http://localhost:8000/oauth/callback"
scopes = [
    "https://www.googleapis.com/auth/youtube.upload",
]

instagram_client_id = os.getenv("INSTAGRAM_APP_ID")
instagram_client_secret = os.getenv("INSTAGRAM_APP_SECRET")

facebook_redirect_uri = "http://localhost:8000/facebook/oauth/callback"
facebook_scopes = ["user_profile"]


# Endpoint to initiate the OAuth 2.0 flow
@app.get("/oauth/login")
async def initiate_oauth():
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
    auth_url, _ = flow.authorization_url(prompt="consent")
    return {"auth_url": auth_url}


# Endpoint to handle the OAuth callback
@app.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
):
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

        # You can store the tokens securely or use them for API requests here
        # For example, you can return them as a JSON response to your frontend
        print(access_token)
        print(refresh_token)
        return {"access_token": access_token, "refresh_token": refresh_token}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")


@app.get("/facebook/oauth/login")
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
@app.get("/facebook/oauth/callback")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
