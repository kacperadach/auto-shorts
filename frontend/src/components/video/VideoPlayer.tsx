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
import segments from "./segments.json";
import portraitSceneBoxes from "./portrait_scene_boxes.json";
import { CroppingBox } from "../../lib/types";
import { initiate_oauth_youtube, initiate_oauth_facebook } from "../../lib/api";

const FPS = 30;

const PRIMARY_URL =
  "https://auto-shorts-storage.s3.amazonaws.com/video/e0be2e64-9edf-47da-93d6-215b0f10557d.mp4";

const SECONDARY_URL =
  "https://auto-shorts-storage.s3.amazonaws.com/video/0fb494f4-73c4-45fb-8686-90201058297a.mp4";

const DURATION = 41;

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
        transform: "scale(0.4)",
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
              width={1080}
              height={1920}
              highlightColor="#33FF52"
              secondaryColor="#FF3352"
              segments={segments}
              croppingBoxes={portraitSceneBoxes}
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
      <div>
        <button
          style={{ fontSize: "64px" }}
          onClick={async () => {
            const response = await initiate_oauth_youtube();
            if (!response.success) {
              console.log("Failed to initiate oauth");
              return;
            }

            const { auth_url } = response.data;

            window.open(auth_url, "_blank");
          }}
        >
          Initiate OAuth Google
        </button>
      </div>
      <div>
        <button
          style={{ fontSize: "64px" }}
          onClick={async () => {
            const response = await initiate_oauth_facebook();
            if (!response.success) {
              console.log("Failed to initiate oauth");
              return;
            }

            const { auth_url } = response.data;

            window.open(auth_url, "_blank");
          }}
        >
          Initiate OAuth Facebook
        </button>
      </div>
    </div>
  );
}
