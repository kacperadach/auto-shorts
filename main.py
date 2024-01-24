from dotenv import load_dotenv

load_dotenv()

import random
import uuid
import os
import json
from time import sleep
from pathlib import Path


import asyncio

from download import (
    download_youtube_audio,
    download_youtube_info,
    download_youtube_vod,
    extract_clip_2_step_mp4,
)
from s3 import upload_file_to_s3
from whisper import call_whisper_runpod, get_whisper_status_runpod, parse_whisper_output
from llm.llm import (
    get_clips,
)
from llm.prompts.clipping import CLIPPING_PROMPT_V1_SYSTEM
from aspect_ratio.conversion import compute_portrait_square_bboxes_with_scenes

# Get the directory of the current script
script_directory = Path(__file__).parent.absolute()

S3_URL = "https://auto-shorts-storage.s3.amazonaws.com/"


async def download_audio_and_upload_to_s3(url, unique_id):
    audio_file_name = download_youtube_audio(url)
    audio_file_extension = os.path.splitext(audio_file_name)[1]
    full_audio_path = os.path.join(script_directory, audio_file_name)
    s3_object_name = f"audio/{unique_id}{audio_file_extension}"

    await upload_file_to_s3(full_audio_path, s3_object_name)

    return S3_URL + s3_object_name


async def transcribe_audio(audio_s3_url: str):
    response = call_whisper_runpod(audio_s3_url)
    sleep(2)

    output = None
    finished = False
    while not finished:
        body = get_whisper_status_runpod(response["id"])
        status = body["status"]
        if status == "FAILED":
            print("FAILED")
            break

        if status == "COMPLETED":
            print("COMPLETED")
            output = body["output"]
            break

        sleep(2)

    print(output)
    with open(os.path.join(script_directory, "whisper_output.json"), "w") as f:
        f.write(json.dumps(output, indent=4))

    return parse_whisper_output(output)


async def main(url: str, secondary_url: str):
    unique_id = uuid.uuid4()

    # audio_s3_url = await download_audio_and_upload_to_s3(url, unique_id)
    # print(audio_s3_url)
    # segments = await transcribe_audio(audio_s3_url)
    # print(segments)

    output_file = os.path.join(script_directory, "whisper_output.json")
    with open(output_file, "r") as f:
        output = json.loads(f.read())

    segments = parse_whisper_output(output)
    # print(len(segments))

    # clips = await get_clips(segments, "Anything interesting")
    # print(clips)

    clips = [
        {"start": 289.0, "end": 330.0},
        {"start": 460.0, "end": 492.0},
        {"start": 1114.0, "end": 1148.0},
        {"start": 1177.0, "end": 1208.0},
        {"start": 1231.0, "end": 1263.0},
        {"start": 1754.0, "end": 1786.0},
        {"start": 3699.0, "end": 3769.0},
        {"start": 3793.0, "end": 3883.0},
        {"start": 4857.0, "end": 4895.0},
    ]

    # random_clip = clips[random.randint(0, len(clips) - 1)]

    random_clip = clips[0]
    # print("clip selected", random_clip)

    # video_file_name = download_youtube_vod(url, resolution=1080, ext="mp4")
    # full_video_path = os.path.join(script_directory, video_file_name)
    # final_output_path = extract_clip_2_step_mp4(
    #     full_video_path, random_clip["start"], random_clip["end"]
    # )

    # video_file_extension = os.path.splitext(final_output_path)[1]
    # s3_object_name = f"video/{unique_id}{video_file_extension}"

    # await upload_file_to_s3(final_output_path, s3_object_name)

    clip_duration = random_clip["end"] - random_clip["start"]

    info = download_youtube_info(secondary_url)

    secondary_duration = info.get("duration", 0)

    if secondary_duration == 0 or secondary_duration < clip_duration:
        raise Exception("secondary video is too short")

    start = random.randint(0, secondary_duration - clip_duration)
    end = start + clip_duration

    video_file_name = download_youtube_vod(
        secondary_url, resolution=1080, info=info, ext="mp4"
    )
    full_video_path = os.path.join(script_directory, video_file_name)
    final_output_path = extract_clip_2_step_mp4(full_video_path, start, end)

    video_file_extension = os.path.splitext(final_output_path)[1]
    s3_object_name = f"video/{unique_id}{video_file_extension}"

    await upload_file_to_s3(final_output_path, s3_object_name)

    # full_video_path = os.path.join(script_directory, "tmp", "video.mp4")

    # (
    #     square_scene_boxes,
    #     portrait_scene_boxes,
    #     square_tracking_boxes,
    #     portrait_tracking_boxes,
    # ) = compute_portrait_square_bboxes_with_scenes(full_video_path)
    # print(portrait_scene_boxes)

    # I have: transcription, bounding-boxes, video clip


if __name__ == "__main__":

    async def run():
        url = "https://www.youtube.com/watch?v=M-rIrn8aLuc"
        secondary_url = "https://www.youtube.com/watch?v=dVdTWry7UNg"
        await main(url, secondary_url)

    asyncio.run(run())

    # full_path_to_audio = os.path.join(script_directory, "audio.m4a")
    # await upload_file_to_s3(full_path_to_audio, "audio.m4a")
    # audio_url = "https://auto-shorts-storage.s3.amazonaws.com/audio.m4a"
    # response = call_whisper_runpod(audio_url)
    # sleep(2)

    # output = None
    # finished = False
    # while not finished:
    #     body = get_whisper_status_runpod(response["id"])
    #     status = body["status"]
    #     if status == "FAILED":
    #         print("FAILED")
    #         break

    #     if status == "COMPLETED":
    #         print("COMPLETED")
    #         output = body["output"]
    #         break

    #     sleep(2)

    # print(output)
    # with open(os.path.join(script_directory, "whisper_output.json"), "w") as f:
    #     f.write(json.dumps(output, indent=4))

    # output_file = os.path.join(script_directory, "whisper_output.json")
    # with open(output_file, "r") as f:
    #     output = json.loads(f.read())

    # segments = parse_whisper_output(output)
    # # print(json.dumps([a.dict() for a in parse_whisper_output(output)]))

    # prompt = format_clipping_prompt(segments, "Anything interesting")

    # print(prompt)
    # response = call_openai(prompt, system_prompt=CLIPPING_PROMPT_V1_SYSTEM, model="gpt-4")

    # print(response)

    # print(download_youtube_audio("https://www.youtube.com/watch?v=dh8j8XEsZ2g"))

    # download_youtube_vod(
    #     "https://www.youtube.com/watch?v=dh8j8XEsZ2g", resolution=1080, ext="mp4"
    # )
    # video = 'video.webm'
