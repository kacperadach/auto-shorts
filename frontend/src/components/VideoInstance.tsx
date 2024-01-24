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

  return (
    <div
      style={{ width: `${width}px`, height: `${height}px`, overflow: "hidden" }}
    >
      <div style={{ position: "relative" }}>
        <OffthreadVideo src={url} muted={muted} style={{ position: "absolute"}} />
      </div>
    </div>
  );
}
