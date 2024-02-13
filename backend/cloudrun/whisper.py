# from dotenv import load_dotenv

# load_dotenv()

import os
from time import sleep

import requests
from pydantic import BaseModel

from runpod import call_and_poll_runpod
from models import TextSegment, TranscriptionSegment


def get_segments_for_clip(segments, start, end):
    clip_segments = []
    for segment in segments:
        if (
            (segment.start < end and segment.start >= start)
            or segment.end > start
            and segment.end <= end
        ):
            clip_segments.append(
                TranscriptionSegment(
                    start=segment.start - start,
                    end=segment.end - start,
                    text=segment.text,
                    word_timings=[
                        TextSegment(
                            start=word.start - start,
                            end=word.end - start,
                            text=word.text,
                        )
                        for word in segment.word_timings
                    ],
                )
            )
    return clip_segments


def break_up_segments_for_subtitles(segments, max_duration=5, max_words=4, max_characters=30):
    final_segments = []

    for segment in segments:
        if (
            segment.end - segment.start <= max_duration
            and len(segment.word_timings) <= max_words
            and len(" ".join([word.text for word in segment.word_timings])) <= max_characters
        ):
            final_segments.append(segment)
            continue

        # break up by words or duration or both

        broken_up_segments = []
        words = [word for word in segment.word_timings]

        segment = None
        while len(words) > 0:
            if segment and (
                segment.end - segment.start >= max_duration
                or len(segment.word_timings) >= max_words
                or len(" ".join([word.text for word in segment.word_timings])) >= max_characters
            ):
                broken_up_segments.append(segment)
                segment = None
                continue

            current_word = words.pop(0)
            if segment is None:
                segment = TranscriptionSegment(
                    start=current_word.start,
                    end=current_word.end,
                    text=current_word.text,
                    word_timings=[current_word],
                )
            elif (
                len(" ".join([word.text for word in segment.word_timings]))
                + len(current_word.text)
                >= max_characters
            ):
                broken_up_segments.append(segment)
                segment = TranscriptionSegment(
                    start=current_word.start,
                    end=current_word.end,
                    text=current_word.text,
                    word_timings=[current_word],
                )
            else:
                segment.end = current_word.end
                segment.text += " " + current_word.text
                segment.word_timings.append(current_word)

        if segment:
            broken_up_segments.append(segment)

        final_segments.extend(broken_up_segments)

    return final_segments


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

        output_segments.append(
            TranscriptionSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"],
                word_timings=word_timings,
            )
        )

    return output_segments


async def transcribe_audio(audio_s3_url: str):
    body = WhisperBody(
        input=WhisperInput(audio=audio_s3_url, transcription=None, word_timestamps=True)
    )
    output = call_and_poll_runpod(MODEL_ID, body.dict())
    if output:
        return parse_whisper_output(output)


# if __name__ == "__main__":
#     from llm.llm import get_clips

#     async def r():
#         segments = await transcribe_audio(
#             "https://auto-shorts-storage.s3.amazonaws.com/audio/cd362521-363b-45a0-be8c-636941ab8dca.m4a"
#         )
#         # print(format_clipping_system_prompt(64))
#         # print(format_clipping_prompt(segments, "Anything clip worthy", 64))
#         print(await get_clips(segments, "Anything clip worthy"))

#     import asyncio

#     asyncio.run(r())
