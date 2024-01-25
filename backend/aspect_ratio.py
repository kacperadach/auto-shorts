from dotenv import load_dotenv

load_dotenv()

from runpod import call_and_poll_runpod


MODEL_ID = "9zvyi6dfzunsk4"


def convert_aspect_ratio_runpod(url: str):
    return call_and_poll_runpod(MODEL_ID, {"input": {"video_url": url}})


if __name__ == "__main__":
    print(convert_aspect_ratio_runpod(
        "https://auto-shorts-storage.s3.amazonaws.com/video/e0be2e64-9edf-47da-93d6-215b0f10557d.mp4"
    ))
