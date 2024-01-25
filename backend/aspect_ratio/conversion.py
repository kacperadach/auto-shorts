import os
import sys
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)
from collections import namedtuple
import itertools

import cv2
import ffmpeg
import imageio
import numpy as np
from scenedetect import AdaptiveDetector, FrameTimecode, detect
from scipy.ndimage import gaussian_filter
from scipy.signal import medfilt
from scipy.spatial.distance import cdist
import torch
from tqdm import tqdm

from aspect_ratio.tased_net import TASED_v2


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_info(
    filename: Union[str, os.PathLike],
    strict: bool = False,
    remove_corrupt: bool = False,
) -> Dict[str, Any]:
    try:
        probe = ffmpeg.probe(filename)
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        if remove_corrupt:
            print(f"Removing corrupt file: {filename}")
            os.remove(filename)
        if strict:
            sys.exit(1)
        return {}

    video_stream = next(
        (stream for stream in probe["streams"] if stream["codec_type"] == "video"), None
    )
    if video_stream is None:
        print("No video stream found", file=sys.stderr)
        if strict:
            sys.exit(1)
        return {}

    num_frames = video_stream.get("nb_frames")
    if not num_frames:
        try:
            with imageio.get_reader(filename, "ffmpeg") as reader:
                num_frames = int(reader.get_length())
        except OverflowError:
            import decord

            num_frames = len(decord.VideoReader(filename))

    return {
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "num_frames": int(num_frames),
        "fps": eval(video_stream["r_frame_rate"]),
    }


def detect_scenes(
    video_path, min_scene_time=1, show_progress=False, include_last_scene=False
):
    """Detect scenes in a video.

    Args:
        video_path (str): Path to the video file.
        min_scene_time (int): Minimum length of a scene in seconds.
        show_progress (bool): Whether to show progress bar.
        include_last_scene (bool): Whether to include the last scene in the video.
    Returns:
        list: List of scenes in the video.

    Note: if 0 scenes are detected, the entire video is returned as a scene.

    """
    fps = get_info(video_path).get("fps", 30)
    scenes = detect(
        video_path,
        AdaptiveDetector(min_scene_len=fps * min_scene_time),
        show_progress=show_progress,
    )
    if include_last_scene:
        prev_last_scene = scenes[-1]
        prev_last_frame = prev_last_scene[-1].get_frames()
        last_video_frame = get_info(video_path).get("num_frames", prev_last_frame)
        print(f"prev last frame: {prev_last_frame}")
        print(f"last video frame: {last_video_frame}")
        if prev_last_frame != last_video_frame:
            scenes.append(
                (
                    FrameTimecode(prev_last_frame, fps),
                    FrameTimecode(last_video_frame, fps),
                )
            )
    if not scenes:
        scenes = [
            (
                FrameTimecode(0, fps),
                FrameTimecode(get_info(video_path).get("num_frames", 1), fps),
            )
        ]

    return scenes


def chunk(
    iterable: Iterable,
    n: int,
    transform: Callable = None,
    collate_fn: Callable = None,
    step_size: int | None = None,
    drop_last: bool = False,
) -> Iterable:
    """Yield successive n-sized chunks from iterable."""
    if step_size is None:
        step_size = n

    batch = []
    for x in iterable:
        if transform is not None:
            x = transform(x)
        batch.append(x)
        if len(batch) == n:
            if collate_fn:
                yield collate_fn(batch)
            else:
                yield batch
            batch = batch[step_size:]
    if batch and not drop_last:
        if collate_fn:
            batch = collate_fn(batch)
        yield batch


def transform(snippet):
    """stack & noralization"""
    snippet = torch.cat(snippet, dim=-1)
    snippet = snippet.permute(2, 0, 1).float()
    snippet = snippet.mul_(2.0).sub_(255).div(255)

    return snippet.view(1, -1, 3, snippet.size(1), snippet.size(2)).permute(
        0, 2, 1, 3, 4
    )


def process(model, clip, amp: bool = True):
    """process one clip and save the predicted saliency map"""
    with torch.inference_mode(), torch.cuda.amp.autocast(enabled=amp):
        smap = model(clip.to(device)).float().cpu()[0].clamp(0, 1)

    smap = gaussian_filter(smap.numpy(), sigma=7)
    # convert to uint8
    smap = (smap * 255).astype(np.uint8)
    return smap


def compute_highest_intensity_component(img, min_intensity=50):
    _, thresh = cv2.threshold(img, min_intensity, 255, cv2.THRESH_BINARY)

    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        thresh, connectivity=8
    )

    # The first component is the background, so exclude it
    max_label = 1

    max_avg_intensity = np.average(img[labels == 1])

    for i in range(2, num_labels):
        avg_intensity = np.average(img[labels == i])
        if avg_intensity > max_avg_intensity:
            max_label = i
            max_avg_intensity = avg_intensity

    # Create an output image that only includes the component with the highest average intensity
    # output = np.zeros_like(img)
    # output[labels == max_label] = 255
    # gray dot at centroid
    # outputmax_centroid[int(max_centroid[1]), int(max_centroid[0])] = 128
    try:
        max_centroid = centroids[max_label]
    except IndexError:
        return compute_highest_intensity_component(img, min_intensity - 5)

    return max_centroid


def median_filter_centroids(centroids, kernel_size=3):
    x_coords = centroids[:, 0]

    y_coords = centroids[:, 1]

    filtered_x_coords = medfilt(x_coords, kernel_size=kernel_size)
    filtered_y_coords = medfilt(y_coords, kernel_size=kernel_size)

    # Combine the filtered coordinates back into an array of centroids
    filtered_centroids = np.column_stack((filtered_x_coords, filtered_y_coords))
    return filtered_centroids


def interpolate_bounding_boxes(
    bboxes: torch.Tensor, sentinel: int = -1
) -> torch.Tensor:
    """Interpolate bounding boxes that are marked with a sentinel value.

    Args:
        bboxes (torch.Tensor): A tensor of shape (N, 4) where N is the number of bounding boxes.
        sentinel (int): The sentinel value to look for. Defaults to -1.

    Returns:
        torch.Tensor: A tensor of shape (N, 4) where N is the number of bounding boxes.
    """
    valid_indices = torch.where(bboxes[:, 0] != sentinel)[0]
    interpolated_bboxes = bboxes.clone()
    if len(valid_indices) == 0:
        return interpolated_bboxes

    # if first box is not valid, then repeat the first valid box until the first valid box
    if valid_indices[0] != 0:
        interpolated_bboxes[: valid_indices[0]] = interpolated_bboxes[valid_indices[0]]

    # if last box is not valid, then repeat the last valid box until the last valid box
    if valid_indices[-1] != bboxes.shape[0] - 1:
        interpolated_bboxes[valid_indices[-1] :] = interpolated_bboxes[
            valid_indices[-1]
        ]

    # interpolate the bounding boxes between the valid boxes
    for i in range(len(valid_indices) - 1):
        start = valid_indices[i]
        end = valid_indices[i + 1]
        gap = end - start

        if gap > 1:
            start_bbox = bboxes[start]
            end_bbox = bboxes[end]
            interpolation_weights = torch.linspace(0, 1, gap + 1)[:-1].unsqueeze(-1)

            interpolated_values = start_bbox + interpolation_weights * (
                end_bbox - start_bbox
            )
            interpolated_bboxes[start + 1 : end] = interpolated_values[1:]

    return interpolated_bboxes


def upsample_centroids(centroids, step_size):
    """Interpolate centroids to match the original frame rate.

    Args:
        centroids: A list or ndarray of centroids.
        step_size: The number of frames in between each centroid.

    Returns:
        A torch tensor of shape (len(centroids) * step_size, 2) containing the upsampled centroids.

    """
    upsampled_centroids = -1 * torch.ones((len(centroids) * step_size, 2))

    # scatter the centroids into the upsampled array
    upsampled_centroids[::step_size] = torch.from_numpy(centroids)

    # interpolate the centroids
    upsampled_centroids = interpolate_bounding_boxes(upsampled_centroids)

    return upsampled_centroids


def compute_smoothed_centroids(
    centroids: list[np.ndarray] | np.ndarray,
    step_size,
    cluster_threshold=25,
    smoothing_threshold=10,
):
    """Compute smoothed centroids from a list of centroids.

    Args:
        centroids: A list of centroids.
        cluster_threshold: The maximum distance between two centroids to be considered part of the same cluster.
        smoothing_threshold: The maximum distance between two centroids to be collapsed into a single centroid.
    """
    clusters = []
    distances = []
    current_cluster = [centroids[0]]

    for i in range(1, len(centroids)):
        dist = cdist([centroids[i]], [centroids[i - 1]], metric="euclidean")
        if dist <= cluster_threshold:
            current_cluster.append(centroids[i])
        else:
            clusters.append(current_cluster)
            current_cluster = [centroids[i]]

    # Add the last cluster
    if current_cluster:
        clusters.append(current_cluster)

    # Compute the median of each cluster
    median_centroids = np.concatenate(
        [np.median(cluster, axis=0, keepdims=True) for cluster in clusters]
    )
    # compute the distances between the median centroids
    distances = np.linalg.norm(median_centroids[1:] - median_centroids[:-1], axis=1)

    tiled_median_centroids = []
    for i in range(len(median_centroids) - 1):
        num_coords = len(clusters[i]) * step_size
        if distances[i] <= smoothing_threshold:
            coords = -1 * np.ones((num_coords, 2))
            # first coordinate is the median centroid
            coords[0] = median_centroids[i]
            # second coordinate is the median centroid of the next cluster
            coords[-1] = median_centroids[i + 1]
            coords = interpolate_bounding_boxes(torch.from_numpy(coords))
            tiled_median_centroids.append(coords.numpy())
        else:
            tiled_median_centroids.append(np.tile(median_centroids[i], (num_coords, 1)))
    # add the last median centroid
    tiled_median_centroids.append(
        np.tile(median_centroids[-1], (len(clusters[-1]) * step_size, 1))
    )

    return tiled_median_centroids


def compute_timed_scene_centroids(
    video_path,
    model,
    step_size=32,
    temporal_len=32,
    progress_bar=False,
    kernel_size=3,
    min_intensity=50,
    threshold=40,
    min_scene_len=1,
):
    import decord
    import multiprocessing
    import os

    os.environ["OMP_NUM_THREADS"] = str(8 * multiprocessing.cpu_count())

    decord.bridge.set_bridge("torch")

    assert temporal_len == 32, "temporal_len must be 32"
    reader = decord.VideoReader(
        video_path, ctx=decord.cpu(), width=384, height=224, num_threads=0
    )
    fps = reader.get_avg_fps()
    scenes = detect_scenes(video_path, show_progress=True)
    # prepend the first temporal_len-1 frames in reverse order to the beginning of the video reader
    # so that we can compute the first temporal_len-1 frames

    num_scenes = len(scenes)
    total_frames = len(reader)
    for scene_num, (start, end) in enumerate(scenes):
        # bounds of current scene
        start_frame, end_frame = start.get_frames(), end.get_frames()
        start_time = start.get_seconds()

        num_frames = end_frame - start_frame
        end_frame_1 = min(start_frame + temporal_len - 1, total_frames)
        end_frame_2 = min(end_frame, total_frames)

        data_iter = itertools.chain(
            reversed(reader[start_frame:end_frame_1]),
            map(reader.__getitem__, range(start_frame, end_frame_2)),
        )

        num_chunks = (num_frames - temporal_len) // step_size + 1
        scene_centroids = []
        for clip in tqdm(
            chunk(
                data_iter,
                temporal_len,
                step_size=step_size,
                collate_fn=transform,
                drop_last=True,
            ),
            total=num_chunks,
            disable=not progress_bar,
            desc=f"Scene {scene_num+1:02d}/{num_scenes:02d}",
        ):
            smap = process(model, clip)
            scene_centroid = compute_highest_intensity_component(
                smap, min_intensity=min_intensity
            )
            scene_centroids.append(scene_centroid)

        if len(scene_centroids) == 0 and num_frames < temporal_len:
            # TODO: should probably think more deeply about this
            continue

        filtered_scene_centroids = median_filter_centroids(
            np.stack(scene_centroids), kernel_size=kernel_size
        )

        tracking_centroids = [
            median_filter_centroids(
                upsample_centroids(np.stack(scene_centroids), step_size)
            )
        ]

        scene_centroids = compute_smoothed_centroids(
            filtered_scene_centroids,
            step_size,
            cluster_threshold=threshold,
            smoothing_threshold=10,
        )

        num_coords = sum([len(centroid) for centroid in scene_centroids])
        if num_coords > num_frames:
            diff = num_coords - num_frames
            scene_centroids[-1] = scene_centroids[-1][:-diff]

        num_tracking_coords = sum([len(centroid) for centroid in tracking_centroids])
        if num_tracking_coords > num_frames:
            diff = num_coords - num_frames
            tracking_centroids[-1] = tracking_centroids[-1][:-diff]

        scene_centroid_lens = [0] + [len(centroid) for centroid in scene_centroids]
        timestamps = start_time + np.cumsum(scene_centroid_lens) / fps

        # tracking_centroid_lens = [0] + [len(centroid) for centroid in tracking_centroids]
        # tracking_timestamps = start_time + np.cumsum(tracking_centroid_lens) / fps

        tracking_timestamps = np.linspace(
            start_time, start_time + num_frames / fps, num_frames
        )
        yield timestamps, scene_centroids, tracking_timestamps, tracking_centroids


def compute_portrait_from_hcenter(hcenter: int, img_size, new_aspect_ratio=9 / 16):
    """Compute the largest possible crop in the original image given a new aspect ratio and a horizontal center.

    Args:
        hcenters: A tensor of shape [N] containing the horizontal centers of the bounding boxes.
        img_size: A tuple (width, height) representing the size of the original image.
        new_aspect_ratio: The desired aspect ratio of the new crop.

    Returns:
        A tensor of shape [N, 4] containing the largest possible crop in the original image centered
        around the horizontal position of the original bounding boxes and with the desired aspect ratio.
    """
    # assert original aspect ratio is landscape
    assert (img_size[0] / img_size[1]) < 1, "original image is not landscape"

    # compute horizontal center of bbox
    new_width = new_aspect_ratio * img_size[0]
    xmin = hcenter - new_width // 2
    xmax = hcenter + new_width // 2
    ymin, ymax = 0, int(img_size[0])

    # clip to image boundaries and ensure output has proper aspect ratio
    if xmin < 0:
        xmin = 0
        xmax = new_width
    elif xmax > img_size[1]:
        xmax = img_size[1]
        xmin = xmax - new_width
    return int(xmin), ymin, int(xmax), ymax


def normalize_centroid(centroid, size):
    """Normalize a centroid coordinate to [0, 1].

    Args:
        centroid: The centroid to normalize.
        size: height, width of the image.

    Returns:
        The normalized bounding box.
    """
    x, y = centroid
    height, width = size
    return x / width, y / height


def normalize_bbox(bbox, size):
    """Normalize a bounding box to the range [0, 1].

    Args:
        bbox: The bounding box to normalize.
        size: height, width of the image.

    Returns:
        The normalized bounding box.
    """
    xmin, ymin, xmax, ymax = bbox
    height, width = size
    return xmin / width, ymin / height, xmax / width, ymax / height


BBox = namedtuple("BBox", ["start_time", "end_time", "bbox", "is_scene_boundary"])


def _compute_turning_points(data, min_change: float = 0.05, max_drift: float = 0.5):
    """Compute the turning points of a discrete function.

    Args:
        data (list[float]): The discrete function.
    """
    # diff = np.diff(np.concatenate([[data[0]], data, [data[-1]]]))
    diff = np.diff(data)
    curr_direction = 0
    curr_drift = 0
    yield 0
    for i, d in enumerate(diff):
        if abs(curr_drift) > max_drift:
            curr_direction = np.sign(curr_drift)
            if curr_direction != 0:
                curr_drift = 0
                yield i
            curr_direction = 0
        if abs(d) < min_change:
            if curr_direction != 0:
                curr_drift = 0
                yield i
            curr_direction = 0
        if d > min_change:
            if curr_direction != 1:
                curr_drift = 0
                yield i
            curr_direction = 1
        elif d < -min_change:
            if curr_direction != -1:
                curr_drift = 0
                yield i
            curr_direction = -1
        curr_drift += d

    yield len(data) - 1


def compute_turning_points(data, min_change: float = 0.15, max_drift=0.5):
    """Compute the turning points of a discrete function.

    Args:
        data (list[float]): The discrete function.
    """
    return sorted(
        list(
            set(
                _compute_turning_points(
                    data, min_change=min_change, max_drift=max_drift
                )
            )
        )
    )


def get_bbox_center(bbox):
    """Get the center of a bounding box.

    Args:
        bbox (list): bounding box

    Returns:
        tuple: center of bounding box
    """
    x1, y1, x2, y2 = bbox
    return (x1 + x2) / 2, (y1 + y2) / 2


def get_bbox_distance(bbox1, bbox2):
    """Get the distance between two bounding boxes.

    Args:
        bbox1 (list): bounding box 1
        bbox2 (list): bounding box 2

    Returns:
        float: distance between bounding boxes
    """
    x1, y1 = get_bbox_center(bbox1)
    x2, y2 = get_bbox_center(bbox2)
    return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def post_process_scene_bboxes(
    scene_bboxes: list[BBox], min_scene_len=1.0
) -> list[BBox]:
    """Post-process scene bboxes to remove bboxes that are too short.

    If a scene is too short, merge it with the neighboring scene that
    has the closest bounding box.

    Args:
        scene_bboxes (list): list of scene bboxes (start_time, end_time, (x1, y1, x2, y2))
        min_scene_len (float, optional): minimum scene length in seconds. Defaults to 1.0.

    Returns:
        list: list of post-processed scene bboxes
    """
    processed_bboxes = []
    i = 0
    while i < len(scene_bboxes):
        start_time, end_time, bbox, is_scene_boundary = scene_bboxes[i]
        scene_len = end_time - start_time
        if scene_len < min_scene_len:
            # Get the preceding and following bboxes
            prev_bbox = scene_bboxes[i - 1][2] if i > 0 else None
            prev_bbox = processed_bboxes[-1][2] if processed_bboxes else prev_bbox
            next_bbox = scene_bboxes[i + 1][2] if i < len(scene_bboxes) - 1 else None

            # Get the distances to the preceding and following bboxes
            prev_dist = (
                get_bbox_distance(bbox, prev_bbox)
                if prev_bbox is not None
                else float("inf")
            )
            next_dist = (
                get_bbox_distance(bbox, next_bbox)
                if next_bbox is not None
                else float("inf")
            )

            # Merge with the closest bbox
            if prev_dist < next_dist:
                # Merge with preceding bbox
                prev_start_time, _, prev_bbox, _ = processed_bboxes.pop()
                new_scene = BBox(
                    prev_start_time, end_time, prev_bbox, is_scene_boundary
                )
            else:
                # Merge with following bbox
                _, next_end_time, next_bbox, is_scene_boundary = scene_bboxes[i + 1]
                new_scene = BBox(
                    start_time, next_end_time, next_bbox, is_scene_boundary
                )
                i += 1  # Skip the next bbox
            processed_bboxes.append(new_scene)
        else:
            processed_bboxes.append(BBox(start_time, end_time, bbox, is_scene_boundary))
        i += 1
    return processed_bboxes


def load_tased_model(device="cuda"):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    file_weight = os.path.join(curr_dir, "TASED_updated.pt")
    print(file_weight)
    model = TASED_v2()
    if os.path.isfile(file_weight):
        print("loading weight file")
        weight_dict = torch.load(file_weight)
        model_dict = model.state_dict()
        for name, param in weight_dict.items():
            if "module" in name:
                name = ".".join(name.split(".")[1:])
            if name in model_dict:
                if param.size() == model_dict[name].size():
                    model_dict[name].copy_(param)
                else:
                    print(" size? " + name, param.size(), model_dict[name].size())
            else:
                print(" name? " + name)
        print(" loaded")
    else:
        print("weight file?")

    model = model.to(device)
    torch.backends.cudnn.benchmark = False
    model.eval()
    return model


def compute_portrait_square_bboxes_with_scenes(
    video_path,
    model = None,
    step_size=32,
    temporal_len=32,
    progress_bar=False,
    kernel_size=3,
    min_intensity=50,
    threshold=40,
    min_scene_len=1,
) -> tuple[list, list, list, list]:
    
    if model is None:
        model = load_tased_model(device)


    square_scene_boxes = []
    portrait_scene_boxes = []
    square_tracking_boxes = []
    portrait_tracking_boxes = []

    for (
        timestamps,
        scene_centroids,
        tracking_timestamps,
        tracking_centroids,
    ) in compute_timed_scene_centroids(
        video_path,
        model,
        step_size=step_size,
        temporal_len=temporal_len,
        progress_bar=progress_bar,
        kernel_size=kernel_size,
        min_intensity=min_intensity,
        threshold=threshold,
    ):
        new_width = 224 * 16 / 9
        for i, (start, end) in enumerate(zip(timestamps[:-1], timestamps[1:])):
            # These magic numbers are used to convert 224x384 (7/12 aspect ratio) to 224x398 (16/9 aspect ratio)
            # before computing the normalized bounding box
            bounding_box = compute_portrait_from_hcenter(
                scene_centroids[i][0, 0], (224, new_width)
            )
            normalized_bbox = normalize_bbox(bounding_box, (224, new_width))
            portrait_scene_boxes.append(
                BBox(start, end, normalized_bbox, is_scene_boundary=i == 0)
            )
            square_bounding_box = compute_portrait_from_hcenter(
                scene_centroids[i][0, 0], (224, new_width), new_aspect_ratio=1
            )
            normalized_bbox = normalize_bbox(square_bounding_box, (224, new_width))
            square_scene_boxes.append(
                BBox(start, end, normalized_bbox, is_scene_boundary=i == 0)
            )

        # This looks moronically repetitive, but it's actually necessary because the tracking
        # timestamps don't correspond to the scene timestamps

        # extract hcenters
        hcenters = [centroid[0] for centroid in tracking_centroids[0]]

        # compute turning points
        turning_point_inds = compute_turning_points(hcenters)
        tp_timestamps = tracking_timestamps[turning_point_inds]

        for i, (start, end) in enumerate(zip(tp_timestamps[:-1], tp_timestamps[1:])):
            hcenter = hcenters[turning_point_inds[i]]
            bounding_box = compute_portrait_from_hcenter(hcenter, (224, new_width))
            normalized_bbox = normalize_bbox(bounding_box, (224, new_width))

            portrait_tracking_boxes.append(BBox(start, end, normalized_bbox, False))

            square_bounding_box = compute_portrait_from_hcenter(
                hcenter,
                (224, new_width),
                new_aspect_ratio=1,
            )
            normalized_bbox = normalize_bbox(square_bounding_box, (224, new_width))
            square_tracking_boxes.append(BBox(start, end, normalized_bbox, False))

    portrait_scene_boxes = post_process_scene_bboxes(
        portrait_scene_boxes, min_scene_len=min_scene_len
    )
    square_bounding_box = post_process_scene_bboxes(
        square_scene_boxes, min_scene_len=min_scene_len
    )
    return (
        square_scene_boxes,
        portrait_scene_boxes,
        square_tracking_boxes,
        portrait_tracking_boxes,
    )
