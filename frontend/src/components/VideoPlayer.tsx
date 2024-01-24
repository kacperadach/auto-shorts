import { useCallback, useRef } from "react";
import { Player, PlayerRef, RenderPoster } from "@remotion/player";
import {
  useCurrentFrame,
  useVideoConfig,
  AbsoluteFill,
  Sequence,
  Series,
  continueRender,
  delayRender,
} from "remotion";
import { VideoComposition } from "./VideoComposition";

const FPS = 30;

const PRIMARY_URL =
  "https://auto-shorts-storage.s3.amazonaws.com/video/e0be2e64-9edf-47da-93d6-215b0f10557d.mp4";

const SECONDARY_URL =
  "https://auto-shorts-storage.s3.amazonaws.com/video/0fb494f4-73c4-45fb-8686-90201058297a.mp4";

const DURATION = 40;

export function VideoPlayer() {
  const videoPlayerRef = useRef<PlayerRef>(null);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
        marginTop: "2rem",
        transform: "scale(0.5)",
        transformOrigin: "top center",
      }}
    >
      <Player
        ref={videoPlayerRef}
        component={useCallback(
          () => (
            <VideoComposition
              primaryUrl={PRIMARY_URL}
              secondaryUrl={SECONDARY_URL}
              durationInFrames={DURATION * FPS}
              width={1080}
              height={1920}
            />
          ),
          []
        )}
        durationInFrames={DURATION * FPS}
        compositionWidth={1080}
        compositionHeight={1920}
        fps={FPS}
      />
      <div>
        <button
          style={{ fontSize: "64px" }}
          onClick={(e) => {
            if (!videoPlayerRef.current) {
              return;
            }

            videoPlayerRef.current.toggle(e);
          }}
        >
          Play
        </button>
      </div>
    </div>
  );
}