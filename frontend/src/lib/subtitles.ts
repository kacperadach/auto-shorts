import {
  RequiredSubtitleSettings,
  SubtitleSegment,
  SubtitleSegmentText,
  SubtitleSettings,
} from "./types";

export const DEFAULT_SUBTITLE_SETTINGS: SubtitleSettings = {
  highlightColor: "#33FF52",
  secondaryColor: "#FF3352",
  removePunctuation: true,
  allCaps: true,
  maxWordsPerLine: 2,
  fontFamily: "Arial",
  fontSize: 84,
};

export function getSettingsWithDefaults(
  settings: SubtitleSettings
): RequiredSubtitleSettings {
  return {
    ...DEFAULT_SUBTITLE_SETTINGS,
    ...settings,
  } as RequiredSubtitleSettings;
}

export function adjustSegments(
  segments: SubtitleSegment[],
  settings: RequiredSubtitleSettings,
  videoDurationSeconds: number
): SubtitleSegment[] {
  const newSegments: SubtitleSegment[] = [];
  for (const segment of segments) {
    let newSegment: SubtitleSegment = {
      start: segment.start,
      end: segment.end,
      text: segment.text,
      word_timings: [],
    };

    for (const word of segment.word_timings) {
      if (
        (newSegment as SubtitleSegment).word_timings.length >=
        settings.maxWordsPerLine
      ) {
        newSegments.push({
          start: newSegment.word_timings[0].start,
          end: newSegment.word_timings[newSegment.word_timings.length - 1].end,
          text: newSegment.word_timings.map((word) => word.text).join(" "),
          word_timings: newSegment.word_timings,
        });
        newSegment = {
          start: word.start,
          end: word.end,
          text: word.text,
          word_timings: [word],
        };
        continue;
      }

      if (
        word.text.endsWith(".") ||
        word.text.endsWith("!") ||
        word.text.endsWith("?")
      ) {
        newSegment.word_timings.push(word);
        newSegments.push({
          start: newSegment.word_timings[0].start,
          end: newSegment.word_timings[newSegment.word_timings.length - 1].end,
          text: newSegment.word_timings.map((word) => word.text).join(" "),
          word_timings: newSegment.word_timings,
        });
        newSegment = {
          start: 0,
          end: 0,
          text: "",
          word_timings: [],
        };
        continue;
      }

      if (word.start < 0 || word.start > videoDurationSeconds) {
        continue;
      }

      newSegment.word_timings.push(word);
    }

    if (newSegment.word_timings.length > 0) {
      newSegments.push({
        start: newSegment.word_timings[0].start,
        end: newSegment.word_timings[newSegment.word_timings.length - 1].end,
        text: newSegment.word_timings.map((word) => word.text).join(" "),
        word_timings: newSegment.word_timings,
      });
    }
  }

  return newSegments;
}
