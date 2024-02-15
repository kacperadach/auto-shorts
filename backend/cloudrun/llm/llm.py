import os
from typing import Optional
from math import floor, ceil
import json

import requests
from pydantic import BaseModel
from openai import OpenAI

from models import TextSegment, TranscriptionSegment
from llm.prompts.clipping import (
    CLIPPING_PROMPT_V1_USER,
    CLIPPING_PROMPT_V1_SYSTEM,
    CLIPPING_ENTIRE_VIDEO_PROMPT,
    CLIPPING_BATCH_PROMPT,
    MOMENT_PROMPT_V1_SYSTEM,
    MOMENT_PROMPT_V1_USER,
    CLIPPING_PROMPT_V2_SYSTEM,
    CLIPPING_PROMPT_V2_USER,
)


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


def format_clipping_system_prompt(video_length: float, is_entire_video=False):
    return CLIPPING_PROMPT_V1_SYSTEM.format(
        total_video_duration=_format_time(ceil(video_length)),
        batch_prompt=CLIPPING_ENTIRE_VIDEO_PROMPT if is_entire_video else CLIPPING_BATCH_PROMPT,
    )


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


MIN_CLIP_LENGTH = 20
MAX_CLIP_LENGTH = 59


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

    if len(segments) == 0:
        return []

    video_duration = segments[-1].end
    if video_duration < MIN_CLIP_LENGTH:
        return []

    if video_duration < MAX_CLIP_LENGTH:
        return [{"start": segments[0].start, "end": floor(segments[-1].end)}]

    for i in range(0, len(segments), batch_size):
        batch = segments[i : i + batch_size]

        is_entire_video = i == 0 and len(segments) <= batch_size

        prompt = format_clipping_prompt(
            batch,
            topic,
            segments[-1].end,
        )

        system_prompt = format_clipping_system_prompt(
            segments[-1].end, is_entire_video=is_entire_video
        )

        response = call_openai(
            prompt,
            system_prompt=system_prompt,
            model="gpt-4-1106-preview",
        )
        new_clips = parse_clips_response(response.choices[0].message.content)
        if new_clips:
            print("new clips", new_clips)
            all_clips.extend(new_clips)

    return all_clips


def _validate_and_parse_moment_dict(moment_dict: dict):
    if not isinstance(moment_dict, dict):
        return None

    if not "id" in moment_dict or not "rating" in moment_dict:
        return None

    if moment_dict["rating"].lower() not in ["excellent", "great", "good", "neutral"]:
        return None

    return {"id": int(moment_dict["id"]), "rating": moment_dict["rating"].lower()}


def parse_moments_response(response):
    try:
        if isinstance(response, str):
            response = json.loads(response)

        if isinstance(response, list):
            return [
                parsed_clip
                for clip in response
                if (parsed_clip := _validate_and_parse_moment_dict(clip))
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
                if (parsed_clip := _validate_and_parse_moment_dict(clip))
            ]
        print("Invalid moments response:", response)
    except Exception as e:
        print(e)
        return []

    return []


def parse_clips_v2_response(response):
    try:
        if isinstance(response, str):
            response = json.loads(response)

        if not isinstance(response, dict):
            return None

        if "start" not in response or "end" not in response:
            return None

        return {"start": int(response["start"]), "end": int(response["end"])}
    except Exception as e:
        print(e)
        return None


BUFFER_TIME = 0.5  # half second added to start/end to make sure we don't cut off words


async def get_clips_v2(segments, topic, max_clips=5):
    if len(segments) == 0:
        return []

    video_duration = segments[-1].end
    if video_duration < MIN_CLIP_LENGTH:
        return []

    if video_duration < MAX_CLIP_LENGTH:
        return [{"start": segments[0].start, "end": floor(segments[-1].end)}]

    batch_size = 100
    all_moments = []
    for i in range(0, len(segments), batch_size):

        transcription = []

        batch = segments[i : i + batch_size]
        for index, seg in enumerate(batch):
            transcription.append(
                {
                    "id": index,
                    "start": _format_time(floor(seg.start)),
                    "end": _format_time(ceil(seg.end)),
                    "text": seg.text,
                }
            )

        prompt = MOMENT_PROMPT_V1_USER.format(
            topic=topic, transcription=json.dumps(transcription)
        )

        response = call_openai(
            prompt,
            system_prompt=MOMENT_PROMPT_V1_SYSTEM,
            model="gpt-4-1106-preview",
        )

        moments = parse_moments_response(response.choices[0].message.content)

        for moment in moments:
            all_moments.append({"id": int(moment["id"]) + i, "rating": moment["rating"]})

    if not all_moments:
        print("No moments found")
        return []

    rating_order = {"excellent": 1, "great": 2, "good": 3, "neutral": 4}

    sorted_moments = sorted(all_moments, key=lambda x: rating_order[x["rating"]])
    for moment in sorted_moments:
        print(moment)

    clips = []
    for moment in sorted_moments:

        if len(clips) == max_clips:
            break

        segment = segments[moment["id"]]

        segment_middle = segment.start + (segment.end - segment.start) / 2
        if any(clip["start"] < segment_middle < clip["end"] for clip in clips):
            print("Moment already included in another clip")
            continue

        end_id = moment["id"] + 1
        while True:
            if end_id == len(segments):
                break

            if segments[end_id].end - segment.end > MAX_CLIP_LENGTH:
                break

            end_id += 1

        start_id = moment["id"] - 1
        while True:
            if start_id == -1:
                break

            if segment.start - segments[start_id].start > MAX_CLIP_LENGTH:
                break

            start_id -= 1

        potential_clip_segments = segments[start_id + 1 : end_id]

        prompt = CLIPPING_PROMPT_V2_USER.format(
            transcription=json.dumps(
                [
                    {"id": index, "text": seg.text}
                    for index, seg in enumerate(potential_clip_segments)
                ]
            ),
            key_segment={"id": potential_clip_segments.index(segment), "text": segment.text},
        )

        system_prompt = CLIPPING_PROMPT_V2_SYSTEM.format(
            min_clip_length=MIN_CLIP_LENGTH, max_clip_length=MAX_CLIP_LENGTH
        )

        response = call_openai(
            prompt,
            system_prompt=system_prompt,
            model="gpt-4-1106-preview",
        )

        clip = parse_clips_v2_response(response.choices[0].message.content)
        if not clip:
            continue

        print(
            str(
                potential_clip_segments[clip["end"]].end
                - potential_clip_segments[clip["start"]].start
            )
            + ": \n"
            + str([seg.text for seg in potential_clip_segments[clip["start"] : clip["end"]]])
        )

        if clip["start"] > potential_clip_segments.index(segment):
            print("Invalid start, does not include interesting moment")
            continue

        if clip["end"] < potential_clip_segments.index(segment):
            print("Invalid end, does not include interesting moment")
            continue

        # adjust clips boundaries to include buffer time and fit in max clip length

        start = potential_clip_segments[clip["start"]].start
        if clip["start"] > 0:
            print("Adding buffer time to start of clip")
            start = max(start - BUFFER_TIME, potential_clip_segments[clip["start"] - 1].end)

        end = potential_clip_segments[clip["end"]].end

        if end - start > MAX_CLIP_LENGTH:
            print("Clip too long, adjusting")
            end = start + MAX_CLIP_LENGTH
        elif end - start < MIN_CLIP_LENGTH:
            print("Clip too short, adjusting")
            end = start + MIN_CLIP_LENGTH
        elif (
            end + BUFFER_TIME < MAX_CLIP_LENGTH
            and clip["end"] < len(potential_clip_segments) - 1
        ):
            print("Adding buffer time to end of clip")
            end = min(
                end + BUFFER_TIME,
                potential_clip_segments[clip["end"] + 1].start,
            )

        clips.append(
            {
                "start": start,
                "end": end,
            }
        )

    return clips


if __name__ == "__main__":
    pass
