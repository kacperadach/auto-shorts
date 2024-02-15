import os
import subprocess
import shutil
import tempfile
import re
from math import floor, ceil
from uuid import uuid4
from datetime import datetime, timedelta
import enum

import requests
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL

TMP_DIR = "/tmp"

DEFAULT_YT_DLP_ARGS = {
    "quiet": True,
    "noprogress": True,
    "no_warnings": True,
    "ignoreerrors": False,
    "nocheckcertificate": True,
    "check_formats": False,
    "writeinfojson": False,
    "restrictfilenames": True,
}

DEFAULT_YT_DLP_INFO_ARGS = {
    "simulate": True,
    "skip_download": True,
    "dump_single_json": True,
    "no_color": True,
}


class DownloadHook:
    filename = None

    def get_filename(self, info):
        if not self.filename:
            self.filename = info["filename"]


def _get_closest_available_format(
    formats,
    resolution,
    fps=30,
    ext=None,
    vcodec=None,
    # preffered_format_id=None,
):
    try:
        format_ = next(
            (
                format_
                for format_ in formats[::-1]
                if (ext is None or format_.get("ext") == ext)
                and format_.get("height") is not None
                and format_.get("height") <= resolution
                # and format_.get("fps") is not None
                # and round(format_.get("fps")) <= fps
                and (vcodec is None or vcodec in format_.get("vcodec", ""))
            ),
            None,
        )
        if not format_:
            # if there are no available formats with the same extension,
            # find the extension that maintains the same format_type (video or audio)
            # and return the closest
            format_ = None
            for ft in formats:
                if ft.get("format_note") == "DASH audio" or ft.get("ext") == "mhtml":
                    continue
                if ft.get("height") is not None and ft.get("height") <= resolution:
                    format_ = ft
                    break

        return format_
    except Exception as exc:
        print(exc)
        return None


def download_youtube_info(url, ydl_args: dict = {}):
    # def download_ranges(info_dict, ydl):
    #     print(download_ranges)
    #     section = {
    #         "start_time": 0,
    #         "end_time": 10,
    #         "title": "First 10 seconds",
    #         "index": 1,  # if you want to number this section
    #     }
    #     return [section]

    ydl_opts = {
        **DEFAULT_YT_DLP_ARGS,
        **DEFAULT_YT_DLP_INFO_ARGS,
        "no_playlist": True,
        "default_search": "ytsearch",
        **ydl_args,
        # "extractor_args": {
        #     "youtube:search_max_results": 1000,
        # },
    }
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def download_youtube_vod(url, resolution=1080, info=None, ext=None, vcodec=None):
    if not info:
        info = download_youtube_info(url)

    format_ = _get_closest_available_format(
        info["formats"], resolution=resolution, fps=30, ext=ext, vcodec=vcodec
    )
    audio_format = _get_highest_quality_audio_format(
        info["formats"], "m4a" if format_["ext"] == "mp4" else "webm"
    )

    if not format_ or not audio_format:
        print(f"No available formats less than resolution: {resolution}")
        return None

    youtube_download = DownloadHook()

    # Create the template string with the unique ID and placeholders
    outtmpl = "%(id)s_" + str(uuid4()) + ".%(ext)s"

    ydl_opts = {
        **DEFAULT_YT_DLP_ARGS,
        "progress_hooks": [youtube_download.get_filename],
        "paths": {"home": TMP_DIR},
        "no_color": False,
        "no_playlist": False,
        "lazy_playlist": True,
        "default_search": "ytsearch",
        "format": format_["format_id"] + "+" + audio_format["format_id"],
        "outtmpl": outtmpl,
        # "external_downloader": "ffmpeg",
        # "external_downloader_args": {
        #     "ffmpeg_i": [
        #         "-ss",
        #         str(start),
        #         "-to",
        #         str(end),
        #     ]
        # },
        "force_keyframes_at_cuts": True,
        # "download_ranges": download_ranges,
    }

    # if start and end:
    #     def download_ranges(info_dict, ydl):
    #         print("download_ranges")
    #         section = {
    #             "start_time": floor(30),
    #             "end_time": ceil(40),
    #             "title": "",
    #             "index": 1,
    #         }
    #         return [section]

    #     ydl_opts["download_ranges"] = download_ranges

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)

    if not youtube_download.filename:
        print("No filename found")
        return None

    return re.sub(r"\.f\d+", "", youtube_download.filename)


def _get_highest_quality_audio_format(formats, ext="m4a"):
    return next(
        (
            format_
            for format_ in formats[::-1]
            if format_["resolution"] == "audio only" and format_["audio_ext"] == ext
        ),
        None,
    )


def download_youtube_audio(url, info=None, audio_ext="m4a"):
    if not info:
        info = download_youtube_info(url)

    audio_format = _get_highest_quality_audio_format(info["formats"], audio_ext)

    youtube_download = DownloadHook()
    ydl_opts = {
        **DEFAULT_YT_DLP_ARGS,
        "paths": {"home": TMP_DIR},
        "progress_hooks": [youtube_download.get_filename],
        "format": audio_format["format_id"],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)

    return re.sub(r"\.f\d+", "", youtube_download.filename)


def extract_clip(path, start, end):
    file_extension = os.path.splitext(path)[1]

    output_path = path.rsplit(".", 1)[0] + "_trimmed" + file_extension
    try:
        # if file_extension == ".mp4":
        command = [
            "ffmpeg",
            "-i",
            path,  # Input file
            "-ss",
            str(start),  # Start time
            "-to",
            str(end),  # End time
            "-c",
            "copy",  # Copy the stream directly, no re-encoding
            output_path,  # Output file
        ]
        # elif file_extension == ".webm":
        #     command = [
        #         "ffmpeg",
        #         "-i",
        #         path,  # Input file
        #         "-ss",
        #         str(start),  # Start time
        #         "-to",
        #         str(end),  # End time
        #         "-c:v",
        #         "libvpx",  # Video codec for WebM
        #         "-c:a",
        #         "libvorbis",  # Audio codec for WebM
        #         output_path,  # Output file
        #     ]
        # else:
        #     raise ValueError("Unsupported file format")

        # Execute the command
        subprocess.run(command, check=True)
        print(f"Clip extracted successfully to {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except ValueError as e:
        print(e)


# this function first does a rough cut without re-encoding and then a precise cut with re-encoding
def extract_clip_2_step_mp4(path: str, start: int, end: int, buffer=30):
    file_extension = os.path.splitext(path)[1]
    intermediate_output_path = (
        path.rsplit(".", 1)[0] + f"_{int(start)}_{int(end)}" + "_intermediate" + file_extension
    )
    final_output_path = (
        path.rsplit(".", 1)[0] + f"_{int(start)}_{int(end)}" + "_trimmed" + file_extension
    )

    # with tempfile.NamedTemporaryFile(suffix=file_extension, delete=True) as temp_file:
    #     shutil.copy2(path, temp_file.name)
    #     temp_input_path = temp_file.name
    try:
        # Step 1: Fast cut with buffer

        adjusted_start_time = max(0, start - buffer)
        adjusted_end_time = end + buffer
        fast_cut_command = [
            "ffmpeg",
            "-i",
            path,  # Input file
            "-ss",
            str(adjusted_start_time),  # Start time with buffer
            "-to",
            str(adjusted_end_time),  # End time with buffer
            "-c",
            "copy",  # Copy the stream directly, no re-encoding
            intermediate_output_path,  # Intermediate output file
        ]
        subprocess.run(fast_cut_command, check=True)

        # Step 2: Precise cut with re-encoding
        precise_start_time = buffer if start > buffer else start
        precise_end_time = precise_start_time + (end - start)
        precise_cut_command = [
            "ffmpeg",
            "-i",
            intermediate_output_path,  # Intermediate file as input
            "-ss",
            str(precise_start_time),  # Adjusted start time for precise cut
            "-to",
            str(precise_end_time),  # Adjusted end time for precise cut
            "-c:v",
            "libx264",  # Re-encode video
            "-preset",
            "fast",  # Faster encoding preset
            "-crf",
            "28",
            "-c:a",
            "aac",  # Re-encode audio
            final_output_path,  # Final output file
        ]
        subprocess.run(precise_cut_command, check=True)

        print(f"Clip extracted successfully to {final_output_path}")
        return final_output_path
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except ValueError as e:
        print(e)


class ValidationResult(enum.Enum):
    ERROR = "error"
    VALID = "valid"
    INVALID = "invalid"


# TODO: handle premieres
def validate_youtube_url(url: str, repurpose_created_at: float, is_manual: bool):
    def _validate(url):
        info = download_youtube_info(url)

        if not info:
            print(f"Could not find video info for {url}")
            return ValidationResult.ERROR

        if info.get("is_live"):
            print(f"Video is live: {url}")
            return ValidationResult.INVALID

        if info.get("was_live"):
            print(f"Video was livestream: {url}")
            return ValidationResult.INVALID

        if info.get("aspect_ratio") < 1:
            print(f"Video aspect ratio is too small: {url}")
            return ValidationResult.INVALID

        if not is_manual:
            uploaded_at_date_obj = datetime.strptime(info.get("upload_date"), "%Y%m%d")
            repurposer_date_obj = datetime.fromtimestamp(repurpose_created_at) - timedelta(
                days=1
            )
            if uploaded_at_date_obj < repurposer_date_obj:
                return ValidationResult.INVALID

        return ValidationResult.VALID

    try:
        return _validate(url)
    except Exception as exc:
        print(f"Failed to validate {url}: {exc}")
        return ValidationResult.ERROR


def get_channel_info(url: str):
    response = requests.get(url)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the link tag
    channel_link_tag = soup.find(
        "link", {"rel": "alternate", "type": "application/rss+xml", "title": "RSS"}
    )
    channel_name_meta_tag = soup.find("meta", {"property": "og:title", "content": True})
    thumbnail_link_tag = soup.find("link", {"rel": "image_src", "href": True})
    print(channel_link_tag)
    print(channel_name_meta_tag)
    print(thumbnail_link_tag)

    if not channel_link_tag or not channel_name_meta_tag or not thumbnail_link_tag:
        return None

    href = channel_link_tag["href"].split("channel_id=")
    if len(href) != 2:
        return None

    thumbnail = thumbnail_link_tag["href"]
    if not thumbnail:
        return None

    channel_id = href[1]
    return {
        "channel_id": channel_id,
        "thumbnail_url": thumbnail,
        "name": channel_name_meta_tag["content"],
    }


def extract_video_id(youtube_url):
    # Regular expression to extract the video ID from a YouTube URL
    video_id_match = re.search(r"(?<=v=)[^&#]+", youtube_url)
    return video_id_match.group(0) if video_id_match else None


if __name__ == "__main__":
    import json

    info = download_youtube_info("https://www.youtube.com/watch?v=Nht0nWetyf8")
    print(info.get("aspect_ratio") < 1.5)
    with open("info.json", "w") as file:
        file.write(json.dumps(info, indent=4))
