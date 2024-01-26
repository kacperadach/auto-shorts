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
from whisper import (
    parse_whisper_output,
    transcribe_audio,
)
from llm.llm import (
    get_clips,
)
from llm.prompts.clipping import CLIPPING_PROMPT_V1_SYSTEM
from models import TextSegment, TranscriptionSegment

# from aspect_ratio.conversion import compute_portrait_square_bboxes_with_scenes
from render import render_short

# from upload.youtube import (
#     get_access_token_for_youtube,
#     REFRESH_TOKEN,
#     upload_video_to_youtube,
# )
from aspect_ratio import convert_aspect_ratio_runpod

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


def break_up_segments_for_subtitles(
    segments, max_duration=5, max_words=4, max_characters=30
):
    final_segments = []

    for segment in segments:
        if (
            segment.end - segment.start <= max_duration
            and len(segment.word_timings) <= max_words
            and len(" ".join([word.text for word in segment.word_timings]))
            <= max_characters
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
                or len(" ".join([word.text for word in segment.word_timings]))
                >= max_characters
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


MAX_CLIP_LENGTH = 90


async def clip_and_upload_to_s3(
    video_path: str, unique_id: str, start: int, end: int, primary: bool
):
    final_output_path = extract_clip_2_step_mp4(video_path, start, end)
    video_file_extension = os.path.splitext(final_output_path)[1]
    video_type = "primary" if primary else "secondary"
    s3_object_name = (
        f"video/{unique_id}_{video_type}_{start}_{end}{video_file_extension}"
    )
    return await upload_file_to_s3(final_output_path, s3_object_name)


async def run(primary_url: str, secondary_url: str, clip_topic: str, max_clips=6):
    unique_id = str(uuid.uuid4())

    print(f"Downloading audio for {primary_url}")
    audio_s3_url = await download_audio_and_upload_to_s3(primary_url, unique_id)

    print(f"Transcribing audio for {primary_url}: {audio_s3_url}")
    segments = await transcribe_audio(audio_s3_url)

    if not segments:
        print(
            f"Failed to transcribe audio or not dialog for {primary_url}: {audio_s3_url}"
        )
        return

    print(f"Getting clips for {primary_url}: {clip_topic}")
    clips = await get_clips(segments, clip_topic)

    if not clips:
        print(f"No clips found for {primary_url}: {clip_topic}")
        return

    print(f"Found {len(clips)} clips for {primary_url}: {clip_topic}")
    print(clips)

    # TODO: is there a better way to decide? LLM?
    random.shuffle(clips)
    clips = clips[:max_clips]
    print(f"Using clips: {clips}")

    print(f"Downloading primary video: {primary_url}")
    primary_file_name = download_youtube_vod(primary_url, resolution=1080, ext="mp4")
    if not primary_file_name:
        print(f"Failed to download primary video: {primary_url}")
        return

    full_primary_file_path = os.path.join(script_directory, primary_file_name)

    print(f"Downloading secondary video: {secondary_url}")
    secondary_info = download_youtube_info(secondary_url)
    secondary_duration = secondary_info.get("duration", 0)

    if secondary_duration == 0 or secondary_duration < MAX_CLIP_LENGTH:
        raise Exception("secondary video is too short")

    secondary_file_name = download_youtube_vod(
        secondary_url, info=secondary_info, resolution=1080, ext="mp4"
    )
    if not secondary_file_name:
        print(f"Failed to download secondary video: {secondary_url}")
        return

    full_secondary_file_path = os.path.join(script_directory, secondary_file_name)

    # subtitle_segments = [seg.model_dump() for seg in break_up_segments_for_subtitles(segments)]
    subtitle_segments = break_up_segments_for_subtitles(segments)

    rendered_clips = []
    for clip in clips:
        clip_segments = get_segments_for_clip(
            subtitle_segments, clip["start"], clip["end"]
        )
        print(
            f"Segments for clip from {clip['start']} to {clip['end']}: {clip_segments}"
        )
        print(
            f"Clipping primary video from {clip['start']} to {clip['end']}: {full_primary_file_path}"
        )
        primary_s3_url = await clip_and_upload_to_s3(
            full_primary_file_path, unique_id, clip["start"], clip["end"], True
        )

        clip_duration = clip["end"] - clip["start"]
        secondary_start = random.randint(0, secondary_duration - clip_duration)
        secondary_end = secondary_start + clip_duration
        print(
            f"Clipping secondary video from {secondary_start} to {secondary_end}: {full_secondary_file_path}"
        )

        secondary_s3_url = await clip_and_upload_to_s3(
            full_secondary_file_path, unique_id, secondary_start, secondary_end, False
        )

        print(f"Calculating bounding boxes for {primary_url}: {clip}")

        portrait_scene_boxes = convert_aspect_ratio_runpod(primary_s3_url)
        if not portrait_scene_boxes:
            print(f"Failed to calculate bounding boxes for {primary_url}: {clip}")
            continue

        print(portrait_scene_boxes)

        print(f"Rendering video for {primary_url}: {clip}")
        short_url = render_short(
            primary_url=primary_s3_url,
            secondary_url=secondary_s3_url,
            durationInSeconds=clip["end"] - clip["start"],
            segments=[cs.model_dump() for cs in clip_segments],
            cropping_boxes=portrait_scene_boxes,
        )
        print(f"Rendered video: {short_url}")

        rendered_clips.append(short_url)

    print(rendered_clips)

    # TODO: post clips directly to youtube/instagram


#     access_token = get_access_token_for_youtube(REFRESH_TOKEN)

#     upload_video_to_youtube(
#         access_token,
#         "Insane Lux Baron Steal",
#         "Subscribe for more epic clips!",
#         ["leagueoflegends", "lux", "baron"],
#         os.path.join(script_directory, "short.mp4"),
#     )


# if __name__ == "__main__":

#     async def run_async():

#         url = "https://www.youtube.com/watch?v=3JBulHqdBxg"
#         secondary_url = "https://www.youtube.com/watch?v=FtLw54emSbs"
#         await run(url, secondary_url, "fashion")

#     asyncio.run(run_async())

