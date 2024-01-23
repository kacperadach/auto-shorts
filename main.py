from dotenv import load_dotenv

load_dotenv()

import uuid
import os
import json
from time import sleep
from pathlib import Path


import asyncio

from download import download_youtube_audio, download_youtube_info
from s3 import upload_file_to_s3
from whisper import call_whisper_runpod, get_whisper_status_runpod, parse_whisper_output
from llm.llm import (
    format_clipping_prompt,
    call_llama_runpod,
    get_llama_status_runpod,
    call_openai,
)
from llm.prompts.clipping import CLIPPING_PROMPT_V1_SYSTEM

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


async def get_clips(segments, topic):
    prompt = format_clipping_prompt(segments, topic)

    print(prompt)
    response = call_openai(
        prompt, system_prompt=CLIPPING_PROMPT_V1_SYSTEM, model="gpt-4-1106-preview"
    )
    print(response)


async def main(url: str):
    unique_id = uuid.uuid4()

    # audio_s3_url = await download_audio_and_upload_to_s3(url, unique_id)
    # print(audio_s3_url)
    # segments = await transcribe_audio(audio_s3_url)
    # print(segments)

    output_file = os.path.join(script_directory, "whisper_output.json")
    with open(output_file, "r") as f:
        output = json.loads(f.read())

    segments = parse_whisper_output(output)
    print(segments)

    clips = await get_clips(segments[0:100], "Anything interesting")


if __name__ == "__main__":

    async def run():
        url = "https://www.youtube.com/watch?v=M-rIrn8aLuc"
        await main(url)

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
