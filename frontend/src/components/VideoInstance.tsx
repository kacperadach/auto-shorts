import { useState } from "react";
import {
  RemotionMainVideoProps,
  RemotionVideoProps,
  Video,
  OffthreadVideo,
} from "remotion";

interface VideoInstanceProps {
  url: string;
  durationInFrames: number;
  width: number;
  height: number;
  muted: boolean;
}

export function VideoInstance(props: VideoInstanceProps) {
  const { url, durationInFrames, width, height, muted } = props;

  const [videoUrl, setVideoUrl] = useState<string>(url);

  return (
    <div
      style={{ width: `${width}px`, height: `${height}px`, overflow: "hidden" }}
    >
      <div style={{ position: "relative" }}>
        <OffthreadVideo
          src={videoUrl}
          muted={muted}
          style={{ position: "absolute", top: "-60px", left: "-420px" }}
          onError={() => {
            setVideoUrl(url + "?t=" + Date.now());
          }}
        />
      </div>
    </div>
  );
}
