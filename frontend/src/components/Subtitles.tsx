import { useMemo } from "react";

import segments from "./segments.json";
import {
  useCurrentFrame,
  useVideoConfig,
  AbsoluteFill,
  Sequence,
  Series,
  continueRender,
  delayRender,
} from "remotion";
import { generateFullLongShadow } from "../lib/textShadow";

const MAX_FONT_MULTIPLIER = 1.75;
const BASE_FONT = 72;

interface SubtitlesProps {
  highlightColor: string;
  secondaryColor: string;
}

export function Subtitles(props: SubtitlesProps) {
  const { highlightColor, secondaryColor } = props;
  const currentFrame = useCurrentFrame();

  const fps = useVideoConfig().fps;

  const currentTime = currentFrame / fps;

  const currentSegment = segments.find((segment) => {
    return currentTime >= segment.start && currentTime <= segment.end;
  });

  const maxSegmentLength = useMemo(() => {
    return segments.reduce((acc, segment) => {
      const segmentLength = segment.word_timings.reduce((acc, word) => {
        const wordLength = word.text.length;
        return acc + wordLength;
      }, 0);
      return segmentLength > acc ? segmentLength : acc;
    }, 0);
  }, [segments]);

  const segmentLength = currentSegment
    ? currentSegment.word_timings.reduce((acc, word) => {
        const wordLength = word.text.length;
        return acc + wordLength;
      }, 0)
    : 0;

  const fontMultiplier = useMemo(() => {
    // Calculate the ratio of the current segment length to the max segment length
    const ratio = segmentLength / maxSegmentLength;

    // Invert the ratio and scale it to the range between 1 and MAX_FONT_MULTIPLIER
    return MAX_FONT_MULTIPLIER - ratio * (MAX_FONT_MULTIPLIER - 1);
  }, [segmentLength, maxSegmentLength]);

  return (
    <div
      style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        fontSize: `${BASE_FONT * fontMultiplier}px`,
        color: "white",
        textShadow: generateFullLongShadow(8, "black").toString(),
        width: "80%",
        fontFamily: "Helvetica",
        fontWeight: "bold",
      }}
    >
      {currentSegment &&
        currentSegment.word_timings.map((wordTiming, index) => {
          const isCurrentWord =
            currentTime >= wordTiming.start && currentTime <= wordTiming.end;

          let color = "white";
          if (isCurrentWord) {
            if (currentSegment.word_timings.length > 2) {
              color = highlightColor;
            } else {
              color = secondaryColor;
            }
          }

          return (
            <span key={index} style={{ color }}>
              {wordTiming.text}
            </span>
          );
        })}
    </div>
  );
}
