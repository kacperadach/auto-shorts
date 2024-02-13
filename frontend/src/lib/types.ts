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

export type RepurposerChannel = {
  id: string;
  name: string;
  thumbnail_url: string;
  youtube_channel_id: string;
  repurposer_id: string;
};

export type SocialMediaAccount = {
  id: string;
  platform: string;
  title: string;
  thumbnail_url: string;
};

export type Repurposer = {
  id: string;
  name: string;
  topic: string;
  secondary_categories: string[];
  social_media_accounts: SocialMediaAccount[];
  channels: RepurposerChannel[];
};

export type RepurposerRun = {
  id: string;
  channel_id: string;
  renders: RenderedVideo[];
  status: string;
  created_at: number;
  run_type: "manual" | "automated";
  thumbnail_url: string;
  video_title: string;
  video_id: string;
};

export type RenderedVideo = {
  id: string;
  s3_url: string;
  duration: number;
};


export const SECONDARY_VIDEO_CATEGORIES = ["slime", "soap", "gta_ramp", "minecraft"];