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


# download audio + upload to s3
# transcribe audio (Runpod)
# Get clips (LLM OpenAI)
# Download both videos (primary + secondary)
# Clip video and upload to S3 (primary + secondary)
# compute bounding boxes for primary clip
# render video (Remotion)
# upload video to youtube (youtube api) + instagram (instagram api)

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


# async def main(url: str, secondary_url: str):
#     unique_id = uuid.uuid4()

#     audio_s3_url = await download_audio_and_upload_to_s3(url, unique_id)
#     print(audio_s3_url)
#     segments = await transcribe_audio(audio_s3_url)
#     print(segments)

#     # output_file = os.path.join(script_directory, "whisper_output.json")
#     # with open(output_file, "r") as f:
#     #     output = json.loads(f.read())

#     # segments = parse_whisper_output(segments)

#     # print(segments)

#     # print(len(segments))

#     # clips = await get_clips(segments, "Anything interesting")
#     # print(clips)

#     clips = [
#         {"start": 289.0, "end": 330.0},
#         {"start": 460.0, "end": 492.0},
#         {"start": 1114.0, "end": 1148.0},
#         {"start": 1177.0, "end": 1208.0},
#         {"start": 1231.0, "end": 1263.0},
#         {"start": 1754.0, "end": 1786.0},
#         {"start": 3699.0, "end": 3769.0},
#         {"start": 3793.0, "end": 3883.0},
#         {"start": 4857.0, "end": 4895.0},
#     ]

#     # random_clip = clips[random.randint(0, len(clips) - 1)]

#     random_clip = clips[0]

#     clip_segments = get_segments_for_clip(segments, random_clip["start"], random_clip["end"])

#     final_clip_segments = break_up_segments_for_subtitles(clip_segments)

#     segments_json = [a.model_dump() for a in final_clip_segments]

#     # with open(os.path.join(script_directory, "segments.json"), "w") as f:
#     #     f.write(json.dumps(segments_json, indent=4))

#     # print("clip selected", random_clip)

#     # video_file_name = download_youtube_vod(url, resolution=1080, ext="mp4")
#     # full_video_path = os.path.join(script_directory, video_file_name)
#     # final_output_path = extract_clip_2_step_mp4(
#     #     full_video_path, random_clip["start"], random_clip["end"]
#     # )

#     # video_file_extension = os.path.splitext(final_output_path)[1]
#     # s3_object_name = f"video/{unique_id}{video_file_extension}"

#     # await upload_file_to_s3(final_output_path, s3_object_name)

#     # clip_duration = random_clip["end"] - random_clip["start"]

#     # info = download_youtube_info(secondary_url)

#     # secondary_duration = info.get("duration", 0)

#     # if secondary_duration == 0 or secondary_duration < clip_duration:
#     #     raise Exception("secondary video is too short")

#     # start = random.randint(0, secondary_duration - clip_duration)
#     # end = start + clip_duration

#     # video_file_name = download_youtube_vod(
#     #     secondary_url, resolution=1080, info=info, ext="mp4"
#     # )
#     # full_video_path = os.path.join(script_directory, video_file_name)
#     # final_output_path = extract_clip_2_step_mp4(full_video_path, start, end)

#     # video_file_extension = os.path.splitext(final_output_path)[1]
#     # s3_object_name = f"video/{unique_id}{video_file_extension}"

#     # await upload_file_to_s3(final_output_path, s3_object_name)

#     # full_video_path = os.path.join(script_directory, "tmp", "video.mp4")

#     # (
#     #     square_scene_boxes,
#     #     portrait_scene_boxes,
#     #     square_tracking_boxes,
#     #     portrait_tracking_boxes,
#     # ) = compute_portrait_square_bboxes_with_scenes(final_output_path)

#     # print(portrait_scene_boxes)

#     # # Convert each namedtuple in the list to a dictionary
#     # portrait_scene_boxes_dicts = [bbox._asdict() for bbox in portrait_scene_boxes]

#     # # Now write the list of dictionaries to a JSON file
#     json_output_path = os.path.join(script_directory, "portrait_scene_boxes.json")
#     # with open(json_output_path, "w") as f:
#     #     json.dump(portrait_scene_boxes_dicts, f, indent=4)

#     with open(json_output_path, "r") as f:
#         portrait_scene_boxes = json.loads(f.read())

#     # short_url = render_short(
#     #     primary_url="https://auto-shorts-storage.s3.amazonaws.com/video/e0be2e64-9edf-47da-93d6-215b0f10557d.mp4",
#     #     secondary_url="https://auto-shorts-storage.s3.amazonaws.com/video/0fb494f4-73c4-45fb-8686-90201058297a.mp4",
#     #     durationInSeconds=41,
#     #     segments=segments_json,
#     #     cropping_boxes=portrait_scene_boxes,
#     # )
#     # print(short_url)

#     access_token = get_access_token_for_youtube(REFRESH_TOKEN)

#     upload_video_to_youtube(
#         access_token,
#         "Insane Lux Baron Steal",
#         "Subscribe for more epic clips!",
#         ["leagueoflegends", "lux", "baron"],
#         os.path.join(script_directory, "short.mp4"),
#     )


if __name__ == "__main__":

    async def run_async():
        # 23.710 - before Runpod balance
        # 23.654 - after Runpod balance

        url = "https://www.youtube.com/watch?v=TNyPVm5AVoo"
        secondary_url = "https://www.youtube.com/watch?v=q9BtYEnrkg4"
        await run(url, secondary_url, "fashion")

    asyncio.run(run_async())

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
