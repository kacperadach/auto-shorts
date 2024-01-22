from dotenv import load_dotenv

load_dotenv()

import os
import json
from time import sleep
from pathlib import Path


import asyncio

from download import download_youtube_audio, download_youtube_info
from s3 import upload_file_to_s3
from whisper import call_whisper_runpod, get_whisper_status_runpod, parse_whisper_output

# Get the directory of the current script
script_directory = Path(__file__).parent.absolute()

if __name__ == "__main__":

    async def run():
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

        output_file = os.path.join(script_directory, "whisper_output.json")
        with open(output_file, "r") as f:
            output = json.loads(f.read())

        print(json.dumps([a.dict() for a in parse_whisper_output(output)]))


        

    asyncio.run(run())
    # print(download_youtube_audio("https://www.youtube.com/watch?v=dh8j8XEsZ2g"))

    # download_youtube_vod(
    #     "https://www.youtube.com/watch?v=dh8j8XEsZ2g", resolution=1080, ext="mp4"
    # )
    # video = 'video.webm'
