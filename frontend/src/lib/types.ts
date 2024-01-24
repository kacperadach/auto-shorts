export type SubtitleSegmentText = {
  text: string;
  start: number;
  end: number;
};

export type SubtitleSegment = SubtitleSegmentText & {
  word_timings: SubtitleSegmentText[];
};

export type CroppingBox = {
  start_time: number;
  end_time: number;
  bbox: number[];
};
