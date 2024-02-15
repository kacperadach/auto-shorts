import { Composition, getInputProps } from "remotion";

import { CroppingBox, SubtitleSegment } from "../lib/types";
import { VideoComposition } from "../components/video/VideoComposition";

const COMPOSITION_ID = "VideoComposition";
const FPS = 30;

const SERVE_URL =
  "https://remotionlambda-useast1-znpird87xb.s3.us-east-1.amazonaws.com/sites/video-composition/index.html";

interface VideoRenderProps {
  primaryUrl: string;
  secondaryUrl: string;
  durationInSeconds: number;
  width: number;
  height: number;
  highlightColor: string;
  secondaryColor: string;
  segments: SubtitleSegment[];
  croppingBoxes: CroppingBox[];
}

export default function VideoRender() {
  const {
    primaryUrl,
    secondaryUrl,
    durationInSeconds,
    width,
    height,
    highlightColor,
    secondaryColor,
    segments,
    croppingBoxes,
  } = getInputProps() as unknown as VideoRenderProps;

  return (
    <>
      <Composition
        id={COMPOSITION_ID}
        durationInFrames={Math.min(
          Math.ceil(durationInSeconds * FPS),
          59 * FPS - 1 // always less than 59 seconds
        )}
        fps={FPS}
        width={1080}
        height={1920}
        component={() => (
          <VideoComposition
            primaryUrl={primaryUrl}
            secondaryUrl={secondaryUrl}
            width={width}
            height={height}
            highlightColor={highlightColor}
            secondaryColor={secondaryColor}
            segments={segments}
            croppingBoxes={croppingBoxes}
          />
        )}
      />
    </>
  );
}
