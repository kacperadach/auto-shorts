

## Automatic Shorts creation/posting


# Listen for youtube channel uploads (https://developers.google.com/youtube/v3/guides/push_notifications)

On new upload:
- Need to get transcription of the video to determine repurposable clips
    - download or maybe some API (https://developers.google.com/youtube/v3/docs/captions/download)
- Use transcription to find "clippable" moment(s) start/end timestamps
- Download video with yt-dlp
- Clip video with FFMPEG
- Aspect Ratio conversion AI (can use center at beginning)
- pick ADHD video on the bottom half
- Use captions to add subtitles
- render with Remotion
- post to Social Media (shorts/tiktok/insta)