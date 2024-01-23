import os
from typing import Optional
from math import floor, ceil
import json

import requests
from pydantic import BaseModel
from openai import OpenAI

from models import TextSegment, TranscriptionSegment
from llm.prompts.clipping import CLIPPING_PROMPT_V1_USER


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


def _format_time(seconds_float):
    # Convert float to integer
    total_seconds = int(seconds_float)

    # Calculate hours, minutes, and seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Format the time in HH:MM:SS
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_clipping_prompt(segments: list[TranscriptionSegment], topic: str):
    # potentiall format timestamps
    # formatted_segments = "\n".join(
    #     [
    #         f"{_format_time(floor(s.start))}-{_format_time(ceil(s.end))}:{s.text}"
    #         for s in segments
    #     ]
    # )

    formatted_segments = json.dumps([
        {
            "start": _format_time(floor(s.start)),
            "end": _format_time(ceil(s.end)),
            "text": s.text,
        }
        for s in segments
    ])

    return CLIPPING_PROMPT_V1_USER.format(topic=topic, transcription=formatted_segments)


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
    print(response.json())
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
