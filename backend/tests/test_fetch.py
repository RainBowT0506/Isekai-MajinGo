from youtube_transcript_api import YouTubeTranscriptApi

video_id = "Vr0pc63j7jw"
try:
    print(f"Fetching transcript for {video_id}...")
    t = YouTubeTranscriptApi.list_transcripts(video_id)
    ja_sub = t.find_generated_transcript(['ja'])
    data = ja_sub.fetch()
    print(f"Got {len(data)} items!")
    print(data[:3])
except Exception as e:
    import traceback
    traceback.print_exc()

video_id_2 = "dQw4w9WgXcQ"
try:
    print(f"Fetching transcript for {video_id_2}...")
    t = YouTubeTranscriptApi.list_transcripts(video_id_2)
    en_sub = t.find_transcript(['en'])
    data = en_sub.fetch()
    print(f"Got {len(data)} items!")
    print(data[:3])
except Exception as e:
    import traceback
    traceback.print_exc()
