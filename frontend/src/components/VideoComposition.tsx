import { AbsoluteFill } from "remotion";
import { VideoInstance } from "./VideoInstance";
import { Subtitles } from "./Subtitles";
import { CroppingBox, SubtitleSegment } from "../lib/types";

interface VideoCompositionProps {
  primaryUrl: string;
  secondaryUrl: string;
  width: number;
  height: number;
  highlightColor: string;
  secondaryColor: string;
  segments: SubtitleSegment[];
  croppingBoxes: CroppingBox[];
}

export function VideoComposition(props: VideoCompositionProps) {
  const {
    primaryUrl,
    secondaryUrl,
    width,
    height,
    highlightColor,
    secondaryColor,
    segments,
    croppingBoxes,
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
          width={width}
          height={height / 2}
          muted={false}
          croppingBoxes={croppingBoxes}
        />

        <VideoInstance
          url={secondaryUrl}
          width={width}
          height={height / 2}
          muted={true}
        />
      </div>
      <Subtitles
        segments={segments}
        highlightColor={highlightColor}
        secondaryColor={secondaryColor}
      />
    </AbsoluteFill>
  );
}
