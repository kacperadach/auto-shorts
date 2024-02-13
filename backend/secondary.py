from dotenv import load_dotenv

load_dotenv()

import asyncio
import os
import uuid
import json
from pathlib import Path
import subprocess
import re

from sqlalchemy import desc

from shared.db.models import SecondaryCategory, SecondaryVideo, get_db_context_manager
import scrapetube
from shared.download import get_channel_info, download_youtube_vod
from shared.s3.s3 import upload_file_to_s3


script_directory = Path(__file__).parent.absolute()


def get_video_info(video_file):
    # Command to extract the frame rate and duration
    cmd = f"ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {video_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    fps, duration = result.stdout.strip().split("\n")

    # Calculate and return FPS and duration
    fps = eval(fps)  # The FPS is typically returned as a fraction (e.g., 30000/1001)
    duration = float(duration)
    return fps, duration


def extract_keyframes(video_file, fps):
    cmd = f"ffprobe -select_streams v -show_frames -show_entries frame=pict_type -of csv {video_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    frames = result.stdout.split("\n")
    keyframes = [i / fps for i, frame in enumerate(frames) if "I" in frame]
    return keyframes


def find_split_points(keyframes, desired_length, video_duration):
    split_points = []
    next_split = desired_length

    for kf in keyframes:
        if kf >= next_split:
            split_points.append(kf)
            next_split += desired_length

        # Stop if we reach the end of the video
        if kf >= video_duration:
            break

    return split_points


CHUNK_DURATION_SECONDS = 120


def split_video(video_file, split_points):
    output_files = []
    unique_id = uuid.uuid4()

    for i, point in enumerate(split_points):
        output_filename = f"output_{unique_id}_{i}.mp4"
        cmd = f"ffmpeg -i {video_file} -ss {point} -c copy -t {CHUNK_DURATION_SECONDS} {output_filename}"
        subprocess.run(cmd, shell=True)
        output_files.append(
            {"file": output_filename, "start": point, "end": point + CHUNK_DURATION_SECONDS}
        )

    return output_files


def get_videos(channel_url: str):
    info = get_channel_info(channel_url)
    if not info:
        raise ValueError(f"Could not get channel info for {channel_url}")

    videos = scrapetube.get_channel(info["channel_id"])
    for video in videos:
        yield "https://www.youtube.com/watch?v=" + video["videoId"]

def get_playlist_videos(playlist_id: str):
    videos = scrapetube.get_playlist(playlist_id)
    for video in videos:
        yield "https://www.youtube.com/watch?v=" + video["videoId"]


async def process_secondary_videos(
    category: SecondaryCategory,
    channel_url: str = None,
    playlist_id: str = None,
    max_videos: int = 100,
):
    current_video_id = 0

    with get_db_context_manager() as db:
        highest_video_id = (
            db.query(SecondaryVideo)
            .filter(SecondaryVideo.category == category.value)
            .order_by(SecondaryVideo.category, desc(SecondaryVideo.video_id))
            .limit(1)
            .one_or_none()
        )
        if highest_video_id:
            current_video_id = highest_video_id.video_id + 1

    count = 0

    videos = None
    if channel_url:
        videos = get_videos(channel_url)
    elif playlist_id:
        videos = get_playlist_videos(playlist_id)

    for video_url in videos:
        with get_db_context_manager() as db:
            existing = (
                db.query(SecondaryVideo)
                .filter(SecondaryVideo.original_url == video_url)
                .limit(1)
                .all()
            )
            if existing:
                print(f"Skipping {video_url}, already processed")
                continue

        count += 1
        if count > max_videos:
            break

        file_name = download_youtube_vod(video_url)
        if not file_name:
            print(f"Could not download {video_url}")
            continue

        full_video_path = os.path.join(script_directory, file_name)
        fps, duration = get_video_info(full_video_path)

        keyframes = extract_keyframes(full_video_path, fps)

        split_points = find_split_points(keyframes, CHUNK_DURATION_SECONDS, duration)

        output_files = split_video(full_video_path, split_points)
        print(output_files)

        for output_file in output_files:
            # upload to S3

            s3_url = await upload_file_to_s3(
                output_file["file"],
                object_name=f"secondary/{category.value}/{output_file['file']}",
            )
            print(f"Uploaded to {s3_url}")

            with get_db_context_manager() as db:
                db.add(
                    SecondaryVideo(
                        category=category.value,
                        video_id=current_video_id,
                        original_url=video_url,
                        original_start_time=output_file["start"],
                        original_end_time=output_file["end"],
                        s3_url=s3_url,
                    )
                )
                db.commit()
            current_video_id += 1


if __name__ == "__main__":
    # asyncio.run(
    #     process_secondary_videos(
    #         SecondaryCategory.SOAP, channel_url="https://www.youtube.com/@ASMRSOAP/videos"
    #     )
    # )
    # asyncio.run(
    #     process_secondary_videos(
    #         SecondaryCategory.GTA_RAMP, playlist_id="PLdxE72LlkFocq2kZMWPppfZMrqOtGtU_a"
    #     )
    # )
    asyncio.run(
        process_secondary_videos(
            SecondaryCategory.MINECRAFT, playlist_id="PLmNH-LEp4uAkoVWlKaAMKU8N-L7CnaOVT"
        )
    )

    asyncio.run(
        process_secondary_videos(
            SecondaryCategory.MINECRAFT,
            channel_url="https://www.youtube.com/@OrbitalNCG/videos",
        )
    )

    # channel = Channel("https://www.youtube.com/channel//videos")
    # print(channel)
    # for v in channel.videos:
    #     print(v)
    # info = download_youtube_info(
    #     "https://www.youtube.com/@TalisaTossell/videos",
    #     ydl_args={"print_to_file": {"video": "video_url"}},
    # )
    # with open("test.json", "w") as f:
    #     f.write(json.dumps(info))


# https://www.youtube.com/playlist?list=PLdxE72LlkFocq2kZMWPppfZMrqOtGtU_a

#   https://www.youtube.com/playlist?list=PLmNH-LEp4uAkoVWlKaAMKU8N-L7CnaOVT

# https://www.youtube.com/@OrbitalNCG/videos

# https://www.youtube.com/@GianLecoMC/videos
