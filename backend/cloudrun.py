import requests


CLOUD_RUN_URL = "https://cloud-run-repurpose-buq7gvugdq-uc.a.run.app"


def call_cloudrun():
    body = {
        "primary_youtube_url": "https://www.youtube.com/watch?v=FfB8LrhdfzY",
        "secondary_youtube_url": "https://www.youtube.com/watch?v=pSleP8aaHG4",
        "topic": "fashion",
    }
    response = requests.post(CLOUD_RUN_URL + "/run", json=body, timeout=30000)
    print(response)


if __name__ == "__main__":
    call_cloudrun()
