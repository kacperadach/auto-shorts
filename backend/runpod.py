import os
from time import sleep

import requests

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")

RUN_URL = "https://api.runpod.ai/v2/{model_id}/run"
STATUS_URL = "https://api.runpod.ai/v2/{model_id}/status/{job_id}"


def get_status_runpod(model_id: str, job_id: str):
    return requests.get(
        STATUS_URL.format(model_id=model_id, job_id=job_id),
        headers={"Authorization": "Bearer " + RUNPOD_API_KEY},
        timeout=30000,
    )


def call_runpod(model_id: str, body: dict):
    return requests.post(
        RUN_URL.format(model_id=model_id),
        json=body,
        headers={"Authorization": "Bearer " + RUNPOD_API_KEY},
        timeout=30000,
    )


def call_and_poll_runpod(model_id: str, body: dict, poll_interval: int = 2):
    response = call_runpod(model_id, body)

    if not (200 <= response.status_code < 300):
        return None

    response_json = response.json()

    sleep(poll_interval)

    output = None

    while True:
        response = get_status_runpod(model_id, response_json["id"])

        if not (200 <= response.status_code < 300):
            return None

        body = response.json()

        status = body["status"]
        if status == "FAILED":
            print("FAILED")
            break

        if status == "COMPLETED":
            print("COMPLETED")
            output = body["output"]
            break

        sleep(poll_interval)

    return output
