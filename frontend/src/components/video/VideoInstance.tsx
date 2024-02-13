import { useMemo, useState } from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  Video,
  OffthreadVideo,
} from "remotion";
import { CroppingBox } from "../../lib/types";

interface VideoInstanceProps {
  url: string;
  width: number;
  height: number;
  muted: boolean;
  croppingBoxes?: CroppingBox[];
}

export function VideoInstance(props: VideoInstanceProps) {
  const { url, width, height, muted, croppingBoxes } = props;

  const [videoUrl, setVideoUrl] = useState<string>(url);

  const frame = useCurrentFrame();
  const fps = useVideoConfig().fps;
  const currentTime = frame / fps;

  const { videoWidth, videoHeight } = useMemo(() => {
    let videoWidth;
    let videoHeight;
    if (croppingBoxes) {
      // videoWidth = 1920 * (1920 / 1080);
      // videoHeight = 1920;
      videoWidth = 1920;
      videoHeight = 1080;
    } else {
      videoWidth = 1920;
      videoHeight = 1080;
    }

    return { videoWidth, videoHeight };
  }, [croppingBoxes]);

  const currentCroppingBox = useMemo(() => {
    if (!croppingBoxes) {
      return null;
    }

    const roundTime = Math.round(currentTime * 100000) / 100000;
    const closestFrame = Math.round(roundTime * fps);
    const closestTime = Math.round((closestFrame / fps) * 100000) / 100000;

    return croppingBoxes.find((croppingBox) => {
      return (
        closestTime >= croppingBox.start_time &&
        closestTime <= croppingBox.end_time
      );
    });
  }, [croppingBoxes, currentTime, fps]);

  const left = useMemo(() => {
    if (!currentCroppingBox) {
      return -420; // based on 1080p 9:8 half video centered
    }

    let croppingLeft = videoWidth * currentCroppingBox.bbox[0];

    return -1 * Math.min(1920 - 1080, croppingLeft);
  }, [currentCroppingBox]);

  // xMin: bboxCoordinateResource.normalized_bbox_coordinates_secondary[0],
  // 		yMin: bboxCoordinateResource.normalized_bbox_coordinates_secondary[1],
  // 		xMax: bboxCoordinateResource.normalized_bbox_coordinates_secondary[2],
  // 		yMax: bboxCoordinateResource.normalized_bbox_coordinates_secondary[3],

  // const { activeBbox, bboxIndex } = useMemo(() => {
  // 	// round to the nearest 100000th and then calculate closest frame based on original video FPS
  // 	const videoFps = video.fps || fps;
  // 	const roundTime = Math.round(currentTime * 100000) / 100000;
  // 	const closestFrame = Math.round(roundTime * videoFps);
  // 	const closestTime = Math.round((closestFrame / videoFps) * 100000) / 100000;
  // 	return findActiveBbox(closestTime, bboxCoordinates);
  // }, [currentTime, bboxCoordinates, video.fps, fps]);

  // videoWidth =
  // 				height * (RESOLUTION_1080P.width / RESOLUTION_1080P.height);
  // 			videoHeight = height;

  return (
    <div
      style={{ width: `${width}px`, height: `${height}px`, overflow: "hidden" }}
    >
      <div style={{ position: "relative" }}>
        <OffthreadVideo
          src={videoUrl}
          muted={muted}
          style={{
            position: "absolute",
            top: "-60px",
            left: `${left}px`,
            width: `${videoWidth}px`,
            height: `${videoHeight}px`,
          }}
          onError={() => {
            setVideoUrl(url + "?t=" + Date.now());
          }}
        />
      </div>
    </div>
  );
}
