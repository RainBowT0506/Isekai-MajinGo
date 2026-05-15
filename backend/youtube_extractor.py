import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
import pykakasi
import html

# Initialize kakasi
kks = pykakasi.kakasi()
import json

def extract_video_id(url: str) -> str:
    """
    Extracts the video ID from a YouTube URL.
    Supports various formats (e.g., youtube.com/watch?v=, youtu.be/).
    """
    pattern_watch = r'(?:v=|/v/|embed/|youtu\.be/)([^&\n?#]+)'
    match = re.search(pattern_watch, url)
    if match:
        return match.group(1)
    
    # Fallback if the URL itself is just an ID
    if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', url):
        return url
        
    raise ValueError(f"Could not extract video ID from URL: {url}")

def fetch_subtitles(video_url: str, languages: list = ['ja', 'zh-Hant', 'en', 'zh-TW']) -> list:
    """
    Fetches the subtitle for the given YouTube URL.
    Attempts to fetch based on language priority.
    """
    video_id = extract_video_id(video_url)
    
    # This will raise an exception if no transcript is found
    # You can also use list() for more granular control
    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id, languages=languages)
    
    results = []
    for s in transcript:
        kakasi_result = kks.convert(s.text)
        romaji_text = " ".join([item['hepburn'] for item in kakasi_result])
        
        html_parts = []
        for item in kakasi_result:
            orig_escaped = html.escape(item['orig'])
            hira_escaped = html.escape(item['hira'])
            # If original text differs from both hiragana and katakana conversions, it likely contains Kanji
            if item['orig'] != item['hira'] and item['orig'] != item['kana']:
                html_parts.append(f"<ruby>{orig_escaped}<rt>{hira_escaped}</rt></ruby>")
            else:
                html_parts.append(orig_escaped)
        furigana_html = "".join(html_parts)
        
        results.append({
            'text': s.text, 
            'start': s.start, 
            'duration': s.duration,
            'romaji': romaji_text,
            'furigana_html': furigana_html
        })
        
    return results

def format_subtitles_json(transcript_list: list) -> str:
    formatter = JSONFormatter()
    return formatter.format_transcript(transcript_list)

if __name__ == "__main__":
    # Test block
    test_url = "https://www.youtube.com/watch?v=Vr0pc63j7jw&list=PL12UaAf_xzfozU6PKHlOwbskdUTFKnGrK&index=7"
    try:
        vid = extract_video_id(test_url)
        print(f"[{vid}] Extracted Video ID!")
        subs = fetch_subtitles(test_url)
        print(f"[{vid}] Successfully fetched {len(subs)} subtitle lines.")
        # Print first 3 lines to verify
        for line in subs[:3]:
            print(f"- {line['start']:.2f}s: {line['text']}")

        print("==================================================")
        print(subs)
    except Exception as e:
        print(f"Error fetching subtitles: {e}")
