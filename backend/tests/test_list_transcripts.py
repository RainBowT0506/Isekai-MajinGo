from youtube_transcript_api import YouTubeTranscriptApi

video_ids = ["Vr0pc63j7jw", "dQw4w9WgXcQ"] # The user's video, and rick roll for control

for vid in video_ids:
    print(f"--- Video: {vid} ---")
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(vid)
        print("Available transcripts:")
        for transcript in transcript_list:
            print(f" - {transcript.language} ({transcript.language_code}) [is_generated: {transcript.is_generated}]")
    except Exception as e:
        print(f"Error: {type(e).__name__} - {e}")
