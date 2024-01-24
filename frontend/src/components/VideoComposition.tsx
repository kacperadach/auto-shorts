import {
  useCurrentFrame,
  useVideoConfig,
  AbsoluteFill,
  Sequence,
  Series,
  continueRender,
  delayRender,
} from "remotion";
import { VideoInstance } from "./VideoInstance";
import { Subtitles } from "./Subtitles";

interface VideoCompositionProps {
  primaryUrl: string;
  secondaryUrl: string;
  durationInFrames: number;
  width: number;
  height: number;
  highlightColor: string;
  secondaryColor: string;
}

export function VideoComposition(props: VideoCompositionProps) {
  const {
    primaryUrl,
    secondaryUrl,
    durationInFrames,
    width,
    height,
    highlightColor,
    secondaryColor,
  } = props;

  return (
    <AbsoluteFill style={{ position: "relative", border: "2px solid black" }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          height: "100%",
        }}
      >
        <VideoInstance
          url={primaryUrl}
          durationInFrames={durationInFrames}
          width={width}
          height={height / 2}
          muted={false}
        />

        <VideoInstance
          url={secondaryUrl}
          durationInFrames={durationInFrames}
          width={width}
          height={height / 2}
          muted={true}
        />
      </div>
      <Subtitles highlightColor={highlightColor} secondaryColor={secondaryColor} />
    </AbsoluteFill>
  );
}
