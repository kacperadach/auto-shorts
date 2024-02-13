from dotenv import load_dotenv

load_dotenv()

import traceback
import random
import uuid
import os
import json
from time import sleep
from pathlib import Path

import asyncio

from shared.download import (
    download_youtube_audio,
    download_youtube_info,
    download_youtube_vod,
    extract_clip_2_step_mp4,
    is_valid_youtube_url,
    extract_video_id,
)
from shared.s3.s3 import upload_file_to_s3
from whisper import (
    parse_whisper_output,
    transcribe_audio,
    break_up_segments_for_subtitles,
    get_segments_for_clip,
)
from models import TextSegment, TranscriptionSegment
from llm.llm import get_clips_v2, MAX_CLIP_LENGTH, MIN_CLIP_LENGTH
from shared.db.models import (
    get_db_context_manager,
    RepurposeRun,
    Repurposer,
    SecondaryVideo,
    SecondaryCategory,
    RunStatus,
)
from shared.slack_bot.slack import send_slack_message
from render import render_short
from aspect_ratio import convert_aspect_ratio_runpod

# from upload.youtube import (
#     get_access_token_for_youtube,
#     REFRESH_TOKEN,
#     upload_video_to_youtube,
# )


# Get the directory of the current script
script_directory = Path(__file__).parent.absolute()

# S3_URL = "https://auto-shorts-storage.s3.amazonaws.com/"


def get_secondary_video(categories: list[str]) -> SecondaryVideo:
    category = random.choice(categories)

    with get_db_context_manager() as db:
        max_video_id = (
            db.query(SecondaryVideo)
            .filter(SecondaryVideo.category == category)
            .order_by(SecondaryVideo.video_id.desc())
            .first()
        )
        if not max_video_id:
            raise Exception(f"No videos found for category: {category}")

        video_id = random.randint(0, max_video_id.video_id)

        video = (
            db.query(SecondaryVideo)
            .filter(SecondaryVideo.category == category)
            .filter(SecondaryVideo.video_id == video_id)
            .one_or_none()
        )
        if not video:
            raise Exception(f"No video found for id: {video_id}")

        return video


async def download_audio_and_upload_to_s3(url, unique_id):
    audio_file_name = download_youtube_audio(url)
    audio_file_extension = os.path.splitext(audio_file_name)[1]
    full_audio_path = os.path.join(script_directory, audio_file_name)
    s3_object_name = f"audio/{unique_id}{audio_file_extension}"
    return await upload_file_to_s3(full_audio_path, s3_object_name)
    # return S3_URL + s3_object_name


async def clip_and_upload_to_s3(
    video_path: str, unique_id: str, start: int, end: int, primary: bool
):
    final_output_path = extract_clip_2_step_mp4(video_path, start, end)
    video_file_extension = os.path.splitext(final_output_path)[1]
    video_type = "primary" if primary else "secondary"
    s3_object_name = f"video/{unique_id}_{video_type}_{start}_{end}{video_file_extension}"
    return await upload_file_to_s3(final_output_path, s3_object_name)


CLIPS_PER_MINUTE = 1 / 5


def get_max_clips(duration: int):
    return max(int((duration / 60) * CLIPS_PER_MINUTE), 1)


def update_run_status(run_id: str, status: RunStatus):
    with get_db_context_manager() as db:
        repurpose_run = db.query(RepurposeRun).filter(RepurposeRun.id == run_id).one_or_none()
        if repurpose_run:
            repurpose_run.status = status.value
            db.add(repurpose_run)
            db.commit()
            db.refresh(repurpose_run)


async def run(run_id: str, video_id: str, channel_id: str, is_manual: bool):
    try:
        await _run(run_id, video_id, channel_id, is_manual)
        update_run_status(run_id, RunStatus.COMPLETED)
    except Exception as e:
        stack_trace = traceback.format_exc()
        send_slack_message(
            f"Failed to run for {run_id}, video: {video_id}: {e}\nStack trace:\n{stack_trace}"
        )
        print(
            f"Failed to run for {run_id}, video: {video_id}: {e}\nStack trace:\n{stack_trace}"
        )
        update_run_status(run_id, RunStatus.FAILED)


async def _run(run_id: str, video_id: str, channel_id: str, is_manual: bool):
    primary_url = f"https://www.youtube.com/watch?v={video_id}"
    send_slack_message(f"Running for {run_id}, video: {primary_url}")

    with get_db_context_manager() as db:
        repurpose_run = db.query(RepurposeRun).filter(RepurposeRun.id == run_id).one_or_none()
        if not repurpose_run:
            send_slack_message(f"Run not found: {run_id}")
            print(f"Run not found: {run_id}")
            return

        repurposer = (
            db.query(Repurposer)
            .filter(Repurposer.id == repurpose_run.repurposer_id)
            .one_or_none()
        )
        if not repurposer:
            send_slack_message(f"Repurposer not found: {repurpose_run.repurposer_id}")
            print(f"Repurposer not found: {repurpose_run.repurposer_id}")
            return

    clip_topic = repurposer.topic
    secondary_categories = repurposer.secondary_categories

    if not is_valid_youtube_url(primary_url, repurposer.created_at, is_manual):
        send_slack_message(f"Invalid primary url: {primary_url}")
        print(f"Invalid primary url: {primary_url}")
        return

    unique_id = str(uuid.uuid4())

    if not repurpose_run.audio_s3_url:
        print(f"Downloading audio for {primary_url}")
        audio_s3_url = await download_audio_and_upload_to_s3(primary_url, unique_id)

        with get_db_context_manager() as db:
            repurpose_run.audio_s3_url = audio_s3_url
            db.add(repurpose_run)
            db.commit()
            db.refresh(repurpose_run)

    if repurpose_run.audio_segments is None:
        print(f"Transcribing audio for {primary_url}: {repurpose_run.audio_s3_url}")
        segments = await transcribe_audio(audio_s3_url)

        with get_db_context_manager() as db:
            repurpose_run.audio_segments = [segment.model_dump() for segment in segments]
            db.add(repurpose_run)
            db.commit()
            db.refresh(repurpose_run)
    else:
        segments = [
            TranscriptionSegment.model_load(segment) for segment in repurpose_run.audio_segments
        ]

    if not segments:
        send_slack_message(
            f"Failed to transcribe audio or no dialog for {primary_url}: {audio_s3_url}"
        )
        print(f"Failed to transcribe audio or no dialog for {primary_url}: {audio_s3_url}")
        return

    if repurpose_run.clips is None:
        print(f"Getting clips for {primary_url}: {clip_topic}")
        clips = await get_clips_v2(
            segments, clip_topic, max_clips=get_max_clips(segments[-1].end - segments[0].start)
        )

        print(f"Found {len(clips)} clips for {primary_url}: {clip_topic}")

        with get_db_context_manager() as db:
            repurpose_run.clips = clips
            db.add(repurpose_run)
            db.commit()
            db.refresh(repurpose_run)

    if not repurpose_run.clips:
        send_slack_message(f"No clips found for {primary_url}: {clip_topic}")
        print(f"No clips found for {primary_url}: {clip_topic}")
        return

    print(f"Downloading primary video: {primary_url}")
    primary_file_name = download_youtube_vod(primary_url, resolution=1080, ext="mp4")
    if not primary_file_name:
        send_slack_message(f"Failed to download primary video: {primary_url}")
        print(f"Failed to download primary video: {primary_url}")
        return

    full_primary_file_path = os.path.join(script_directory, primary_file_name)

    # print(f"Downloading secondary video: {secondary_url}")
    # secondary_info = download_youtube_info(secondary_url)
    # secondary_duration = secondary_info.get("duration", 0)

    # if secondary_duration == 0 or secondary_duration < MAX_CLIP_LENGTH:
    #     send_slack_message(f"Secondary video is too short: {secondary_url}")
    #     raise Exception("secondary video is too short")

    # secondary_file_name = download_youtube_vod(
    #     secondary_url, info=secondary_info, resolution=1080, ext="mp4"
    # )
    # if not secondary_file_name:
    #     send_slack_message(f"Failed to download secondary video: {secondary_url}")
    #     print(f"Failed to download secondary video: {secondary_url}")
    #     return

    # full_secondary_file_path = os.path.join(script_directory, secondary_file_name)

    subtitle_segments = break_up_segments_for_subtitles(segments)

    def get_clip_key(clip):
        return str(clip["start"]) + "_" + str(clip["end"])

    for clip in clips:
        print(
            f"Clipping primary video from {clip['start']} to {clip['end']}: {full_primary_file_path}"
        )
        clip_segments = get_segments_for_clip(subtitle_segments, clip["start"], clip["end"])

        primary_s3_url = repurpose_run.clip_primary_urls.get(get_clip_key(clip))
        if not primary_s3_url:
            primary_s3_url = await clip_and_upload_to_s3(
                full_primary_file_path, unique_id, clip["start"], clip["end"], True
            )
            with get_db_context_manager() as db:
                repurpose_run.clip_primary_urls = {
                    **repurpose_run.clip_primary_urls,
                    get_clip_key(clip): primary_s3_url,
                }
                db.add(repurpose_run)
                db.commit()
                db.refresh(repurpose_run)

        secondary_video = get_secondary_video(secondary_categories)

        portrait_scene_boxes = repurpose_run.clip_bounding_boxes.get(get_clip_key(clip))
        if not portrait_scene_boxes:
            print(f"Calculating bounding boxes for {primary_url}: {clip}")
            portrait_scene_boxes = convert_aspect_ratio_runpod(primary_s3_url)

            with get_db_context_manager() as db:
                repurpose_run.clip_bounding_boxes = {
                    **repurpose_run.clip_bounding_boxes,
                    get_clip_key(clip): portrait_scene_boxes,
                }
                db.add(repurpose_run)
                db.commit()
                db.refresh(repurpose_run)

        if not portrait_scene_boxes:
            print(f"Failed to calculate bounding boxes for {primary_url}: {clip}")
            continue

        print(f"Rendering video for {primary_url}: {clip}")
        render_info = render_short(
            primary_url=primary_s3_url,
            secondary_url=secondary_video.s3_url,
            durationInSeconds=clip["end"] - clip["start"],
            segments=[cs.model_dump() for cs in clip_segments],
            cropping_boxes=portrait_scene_boxes,
            video_id=video_id,
            channel_id=channel_id,
            repurposer_id=repurpose_run.repurposer_id,
            run_id=run_id,
        )
        print(
            f"Rendering initiated for video: {primary_url}: {clip}, render info: {render_info}"
        )
        send_slack_message(f"Rendering initiated for video: {primary_url}: {clip}")


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
