import os
from time import sleep

import requests
from pydantic import BaseModel

from models import TextSegment, TranscriptionSegment
from runpod import call_and_poll_runpod


# RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
# RUNPOD_URL = "https://api.runpod.ai/v2/faster-whisper/run"
# RUNPOD_STATUS_URL = "https://api.runpod.ai/v2/faster-whisper/status/"

MODEL_ID = "faster-whisper"


class WhisperInput(BaseModel):
    audio: str
    audio_base64: str = None
    model: str = "base"
    transcription: str | None = "plain_text"
    translate: bool = False
    language: str = "en"
    temperature: int = 0
    best_of: int = 5
    beam_size: int = 5
    patience: int = 1
    suppress_tokens: str = "-1"
    condition_on_previous_text: bool = False
    temperature_increment_on_fallback: float = 0.2
    compression_ratio_threshold: float = 2.4
    logprob_threshold: int = -1
    no_speech_threshold: float = 0.6
    word_timestamps: bool = False


class WhisperBody(BaseModel):
    input: WhisperInput
    enable_vad: bool = False


# def call_whisper_runpod(audio_file_path: str):
#     body = WhisperBody(
#         input=WhisperInput(audio=audio_file_path, transcription=None, word_timestamps=True)
#     )
#     response = requests.post(
#         RUNPOD_URL,
#         json=body.dict(),
#         headers={"Authorization": "Bearer " + RUNPOD_API_KEY},
#         timeout=30000,
#     )
#     print(response.json())
#     return response.json()


# def get_whisper_status_runpod(job_id: str):
#     return requests.get(
#         RUNPOD_STATUS_URL + job_id,
#         headers={"Authorization": "Bearer " + RUNPOD_API_KEY},
#         timeout=30000,
#     ).json()


def parse_whisper_output(output: dict) -> list[TranscriptionSegment]:
    output_segments = []

    word_index = 0
    for index, segment in enumerate(output["segments"]):
        word_timings = []

        while word_index < len(output["word_timestamps"]) and (
            (
                output["word_timestamps"][word_index]["start"] >= segment["start"]
                and output["word_timestamps"][word_index]["start"] < segment["end"]
            )
            or (
                output["word_timestamps"][word_index]["end"] > segment["start"]
                and output["word_timestamps"][word_index]["end"] <= segment["end"]
            )
        ):
            word_timings.append(
                TextSegment(
                    start=output["word_timestamps"][word_index]["start"],
                    end=output["word_timestamps"][word_index]["end"],
                    text=output["word_timestamps"][word_index]["word"],
                )
            )
            word_index += 1

        # if not word_timings:
        #     print(output["segments"][index - 1])
        #     print(segment)
        #     try:
        #         print(output["word_timestamps"][word_index])
        #     except Exception:
        #         pass
        #     raise Exception("No word timings found for segment")

        output_segments.append(
            TranscriptionSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"],
                word_timings=word_timings,
            )
        )

    print(word_index)

    return output_segments


async def transcribe_audio(audio_s3_url: str):
    body = WhisperBody(
        input=WhisperInput(audio=audio_s3_url, transcription=None, word_timestamps=True)
    )
    output = call_and_poll_runpod(MODEL_ID, body.dict())
    if output:
        return parse_whisper_output(output)
