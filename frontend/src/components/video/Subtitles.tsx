import { useMemo } from "react";

import { useCurrentFrame, useVideoConfig, interpolateColors } from "remotion";
import { generateFullLongShadow } from "../../lib/textShadow";
import { SubtitleSegment, SubtitleSettings } from "../../lib/types";
import { adjustSegments, getSettingsWithDefaults } from "../../lib/subtitles";
import SubtitleWord from "./SubtitleWord";

interface SubtitlesProps {
  segments: SubtitleSegment[];
  settings: SubtitleSettings;
}

export function Subtitles(props: SubtitlesProps) {
  const { segments, settings } = props;
  const currentFrame = useCurrentFrame();

  const config = useVideoConfig();
  const durationInSeconds = config.durationInFrames / config.fps;

  const settingsWithDefaults = useMemo(() => {
    return getSettingsWithDefaults(settings);
  }, [settings]);

  const adjustedSegments: SubtitleSegment[] = useMemo(() => {
    return adjustSegments(segments, settingsWithDefaults, durationInSeconds);
  }, [segments, settingsWithDefaults]);

  const fps = useVideoConfig().fps;

  const currentTime = currentFrame / fps;

  const currentSegment = adjustedSegments.find((segment) => {
    return currentTime >= segment.start && currentTime <= segment.end;
  });

  // const maxSegmentLength = useMemo(() => {
  //   return adjustedSegments.reduce((acc, segment) => {
  //     const segmentLength = segment.word_timings.reduce((acc, word) => {
  //       const wordLength = word.text.length;
  //       return acc + wordLength;
  //     }, 0);
  //     return segmentLength > acc ? segmentLength : acc;
  //   }, 0);
  // }, [adjustedSegments]);

  // const segmentLength = currentSegment
  //   ? currentSegment.word_timings.reduce((acc, word) => {
  //       const wordLength = word.text.length;
  //       return acc + wordLength;
  //     }, 0)
  //   : 0;

  // const fontMultiplier = useMemo(() => {
  //   // Calculate the ratio of the current segment length to the max segment length
  //   const ratio = segmentLength / maxSegmentLength;

  //   // Invert the ratio and scale it to the range between 1 and MAX_FONT_MULTIPLIER
  //   return MAX_FONT_MULTIPLIER - ratio * (MAX_FONT_MULTIPLIER - 1);
  // }, [segmentLength, maxSegmentLength]);

  return (
    <div
      style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        fontSize: `${settingsWithDefaults.fontSize}px`,
        color: "white",
        // textShadow: generateFullLongShadow(6, "black").toString(),
        width: "80%",
        fontFamily: settingsWithDefaults.fontFamily,
        fontWeight: "bold",
        textAlign: "center",
        display: "flex",
        whiteSpace: "pre",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <p style={{ lineHeight: 1.2, whiteSpace: "break-spaces" }}>
        {currentSegment &&
          currentSegment.word_timings.map((wordTiming, index) => {
            let color = "white";
            const wordStartFrame = Math.floor(wordTiming.start * fps);

            const wordEndFrame = Math.ceil(wordTiming.end * fps);

            color = interpolateColors(
              currentFrame,
              [0, wordStartFrame, wordEndFrame, wordEndFrame + 10],
              ["white", "white", settingsWithDefaults.highlightColor, "white"]
            );

            // const isCurrentWord =
            //   currentTime >= wordTiming.start && currentTime <= wordTiming.end;

            // if (isCurrentWord) {
            //   const wordStartFrame = wordTiming.start * fps;
            //   color = interpolateColors(
            //     currentFrame,
            //     [wordStartFrame - 30, wordStartFrame + 30],
            //     ["white", settingsWithDefaults.highlightColor]
            //   );

            //   // color = settingsWithDefaults.highlightColor as string;
            //   // if (currentSegment.word_timings.length > 2) {
            //   //   color = settingsWithDefaults.highlightColor as string;
            //   // } else {
            //   //   color = settingsWithDefaults.secondaryColor as string;
            //   // }
            // }

            let finalText = wordTiming.text;
            if (settingsWithDefaults.allCaps) {
              finalText = wordTiming.text.toUpperCase();
            }

            if (settingsWithDefaults.removePunctuation) {
              finalText = finalText.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "");
            }

            // return (
            //   <span key={index} style={{ color }}>
            //     {finalText}
            //   </span>
            // );
            return (
              <SubtitleWord
                key={index}
                text={{
                  text: finalText,
                  fontSize: settingsWithDefaults.fontSize,
                  fontFamily: settingsWithDefaults.fontFamily,
                }}
              />
            );
          })}
      </p>
    </div>
  );
}
