import requests
import threading


CLOUD_RUN_URL = "https://cloud-run-repurpose-buq7gvugdq-uc.a.run.app"


def _call_cloudrun(run_id: str, video_id: str, channel_id: str, is_manual: bool):
    body = {
        "run_id": run_id,
        "video_id": video_id,
        "channel_id": channel_id,
        "is_manual": is_manual,
    }
    response = requests.post(CLOUD_RUN_URL + "/run", json=body, timeout=1000)
    print(response)


def call_cloudrun(run_id: str, video_id: str, channel_id: str, is_manual: bool = False):
    t = threading.Thread(target=_call_cloudrun, args=(run_id, video_id, channel_id, is_manual))
    t.start()


def _call_cloudrun_upload(repurposer_id: str, rendered_video_id: str, s3_url: str):
    body = {
        "repurposer_id": repurposer_id,
        "rendered_video_id": rendered_video_id,
        "s3_url": s3_url,
    }
    response = requests.post(CLOUD_RUN_URL + "/upload", json=body, timeout=1000)
    print(response)


def call_cloudrun_upload(repurposer_id: str, rendered_video_id: str, s3_url: str):
    t = threading.Thread(
        target=_call_cloudrun_upload, args=(repurposer_id, rendered_video_id, s3_url)
    )
    t.start()


if __name__ == "__main__":
    call_cloudrun(
        "",
        "https://www.youtube.com/watch?v=LqYjiODUgkg",
        "",
    )
