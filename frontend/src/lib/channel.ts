export const YOUTUBE_CHANNEL_REGEX =
  /https:\/\/www\.youtube\.com\/(channel\/[\w-]+|@\w+)(\/.*)?/;

export function isValidYoutubeChannel(url: string) {
  return YOUTUBE_CHANNEL_REGEX.test(url);
}
