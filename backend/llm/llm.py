import os
from typing import Optional
from math import floor, ceil
import json

import requests
from pydantic import BaseModel
from openai import OpenAI

from models import TextSegment, TranscriptionSegment
from llm.prompts.clipping import CLIPPING_PROMPT_V1_USER, CLIPPING_PROMPT_V1_SYSTEM


RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_URL = "https://api.runpod.ai/v2/llama2-13b-chat/run"
RUNPOD_STATUS_URL = "https://api.runpod.ai/v2/llama2-13b-chat/status/"

client = OpenAI()

# {
#     "input": {
#         "prompt": "Who is the president of the United States?",
#         "sampling_params": {
#             "max_tokens": 100,
#             "n": 1,
#             "presence_penalty": 0.2,
#             "frequency_penalty": 0.7,
#             "temperature": 0.3,
#         },
#     }
# }


class LlamaSamplingParams(BaseModel):
    max_tokens: int = 100
    n: int = 1
    presence_penalty: float = 0.2
    frequency_penalty: float = 0.7
    temperature: float = 0.3


class LlamaInput(BaseModel):
    prompt: str
    sampling_params: LlamaSamplingParams


class RunpodLlamaBody(BaseModel):
    input: LlamaInput


def _parse_time(time_str: str):
    # Split the time string into hours, minutes, and seconds
    hours, minutes, seconds = map(int, time_str.split(":"))

    # Calculate the total seconds
    total_seconds = hours * 3600 + minutes * 60 + seconds

    return float(total_seconds)


def _format_time(seconds_float):
    # Convert float to integer
    total_seconds = int(seconds_float)

    # Calculate hours, minutes, and seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Format the time in HH:MM:SS
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_clipping_prompt(
    segments: list[TranscriptionSegment], topic: str, video_length: float
):
    formatted_segments = json.dumps(
        [
            {
                "start": _format_time(floor(s.start)),
                "end": _format_time(ceil(s.end)),
                "text": s.text,
            }
            for s in segments
        ]
    )

    return CLIPPING_PROMPT_V1_USER.format(
        topic=topic,
        transcription=formatted_segments,
        total_video_duration=_format_time(ceil(video_length)),
    )


def call_llama_runpod(prompt: str):
    body = RunpodLlamaBody(
        input=LlamaInput(prompt=prompt, sampling_params=LlamaSamplingParams())
    )
    response = requests.post(
        RUNPOD_URL,
        json=body.dict(),
        headers={"Authorization": "Bearer " + RUNPOD_API_KEY},
        timeout=30000,
    )
    return response.json()


def get_llama_status_runpod(job_id: str):
    return requests.get(
        RUNPOD_STATUS_URL + job_id,
        headers={"Authorization": "Bearer " + RUNPOD_API_KEY},
        timeout=30000,
    ).json()


def call_openai(prompt: str, system_prompt: Optional[str] = None, model="gpt-3.5-turbo"):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    response_format = "text"
    if "4" in model:
        response_format = "json_object"

    return client.chat.completions.create(
        model=model, messages=messages, response_format={"type": response_format}
    )


MIN_CLIP_LENGTH = 30
MAX_CLIP_LENGTH = 90


def _validate_and_parse_clip_dict(clip_dict: dict):
    if not isinstance(clip_dict, dict):
        return None

    if not "start" in clip_dict or not "end" in clip_dict:
        return None

    if not isinstance(clip_dict["start"], str) or not isinstance(clip_dict["end"], str):
        return None

    try:
        start_in_secs = _parse_time(clip_dict["start"])
        end_in_secs = _parse_time(clip_dict["end"])
    except ValueError:
        return None

    if (
        end_in_secs <= start_in_secs
        or end_in_secs - start_in_secs < MIN_CLIP_LENGTH
        or end_in_secs - start_in_secs > MAX_CLIP_LENGTH
    ):
        return None

    return {"start": start_in_secs, "end": end_in_secs}


def parse_clips_response(response):
    try:
        if isinstance(response, str):
            response = json.loads(response)

        if isinstance(response, list):
            return [
                parsed_clip
                for clip in response
                if (parsed_clip := _validate_and_parse_clip_dict(clip))
            ]

        if isinstance(response, dict):
            if len(response.keys()) == 0:
                return []

            clip_key = None
            for key in response.keys():
                if isinstance(response[key], list):
                    clip_key = key
                    break

            if not clip_key:
                return []

            return [
                parsed_clip
                for clip in response[clip_key]
                if (parsed_clip := _validate_and_parse_clip_dict(clip))
            ]
    except Exception as e:
        print(e)
        return []

    return []


async def get_clips(segments, topic):
    all_clips = []
    batch_size = 100
    for i in range(0, len(segments), batch_size):
        prompt = format_clipping_prompt(segments[i : i + batch_size], topic, segments[-1].end)

        response = call_openai(
            prompt, system_prompt=CLIPPING_PROMPT_V1_SYSTEM, model="gpt-4-1106-preview"
        )
        new_clips = parse_clips_response(response.choices[0].message.content)
        if new_clips:
            print("new clips", new_clips)
            all_clips.extend(new_clips)

    return all_clips


if __name__ == "__main__":
    parse_clips_response("")
