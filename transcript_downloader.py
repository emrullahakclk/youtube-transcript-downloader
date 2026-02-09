import os
import sys
import time
import random
import re
import json
import yt_dlp
import requests
import http.cookiejar
from youtube_transcript_api import YouTubeTranscriptApi

# --- CONFIGURATION ---
HISTORY_FILE = "processed_videos.txt"
OUTPUT_DIR = "transcripts"
COOKIES_FILE = "cookies.txt"

# Anti-Ban Constants
SLEEP_MIN = 15          # Minimum sleep between videos
SLEEP_MAX = 25          # Maximum sleep between videos
LONG_SLEEP_DURATION = 180  # 3 minutes for rate limits
BATCH_SIZE = 10         # Take longer break every N videos
BATCH_BREAK_MIN = 60    # Minimum batch break (seconds)
BATCH_BREAK_MAX = 120   # Maximum batch break (seconds)

# Anti-Ban: Randomized delays for more human-like behavior
MICRO_DELAY_MIN = 0.5
MICRO_DELAY_MAX = 2.0

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_history(video_id):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{video_id}\n")

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def seconds_to_timestamp(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"[{m:02d}:{s:02d}]"

def human_delay():
    """Small random delay to simulate human behavior."""
    time.sleep(random.uniform(MICRO_DELAY_MIN, MICRO_DELAY_MAX))

def transcript_to_md(transcript_data, output_path, title):
    """Convert transcript data to markdown with timestamps."""
    try:
        if not transcript_data:
            return False
        
        # Convert to list if needed and get first entry
        entries = list(transcript_data)
        if not entries:
            return False
        
        # Group entries by ~5 second blocks
        grouped_lines = []
        current_block_start = entries[0].start
        current_block_text = []
        
        for entry in entries:
            if entry.start - current_block_start >= 5:
                ts = seconds_to_timestamp(current_block_start)
                grouped_lines.append(f"{ts} {' '.join(current_block_text)}")
                current_block_start = entry.start
                current_block_text = [entry.text]
            else:
                current_block_text.append(entry.text)
        
        # Don't forget the last block
        if current_block_text:
            ts = seconds_to_timestamp(current_block_start)
            grouped_lines.append(f"{ts} {' '.join(current_block_text)}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write("\n".join(grouped_lines))
        return True
    except Exception as e:
        print(f"   [ERROR] Writing MD: {e}")
        return False

def get_playlist_videos(url):
    """Fetch playlist info using yt-dlp (only for metadata, no download)."""
    flat_opts = {
        'extract_flat': True,
        'quiet': True,
        'ignoreerrors': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(flat_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                return list(info['entries'])
            else:
                return [info]
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return []



def download_transcript(video_id, languages=['tr', 'en']):
    """Download transcript using youtube_transcript_api v1.2.4."""
    # Anti-ban: small delay before API call
    human_delay()
    
    # Setup session with cookies if available
    session = requests.Session()
    
    # Critical: Set real browser User-Agent to avoid immediate IP block
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })

    if os.path.exists(COOKIES_FILE):
        try:
            cj = http.cookiejar.MozillaCookieJar(COOKIES_FILE)
            cj.load()
            session.cookies = cj
        except Exception as e:
            print(f"    [WARN] Failed to load cookies: {e}")

    try:
        # Pass session to API constructor
        ytt_api = YouTubeTranscriptApi(http_client=session)
        
        # List available transcripts
        transcript_list = ytt_api.list(video_id)
        
        # Anti-ban: small delay between operations
        human_delay()
        
        # Try to find transcript in preferred languages
        selected_transcript = None
        
        # 1. Search for MANUALLY CREATED
        try:
            selected_transcript = transcript_list.find_manually_created_transcript(languages)
            print(f"    [INFO] Found manual transcript: {selected_transcript.language_code}")
        except:
            pass
        
        # 2. Search for GENERATED if no manual found
        if not selected_transcript:
            try:
                selected_transcript = transcript_list.find_generated_transcript(languages)
                print(f"    [INFO] Found generated transcript: {selected_transcript.language_code}")
            except:
                pass
        
        # 3. Fallback: Any available transcript
        if not selected_transcript:
            try:
                # Get the first available transcript
                for transcript in transcript_list:
                    selected_transcript = transcript
                    print(f"    [INFO] Fallback to available transcript: {transcript.language_code}")
                    break
            except:
                pass
        
        if selected_transcript:
            human_delay()  # Anti-ban: delay before fetch
            return selected_transcript.fetch()
        
        print("    [WARN] No suitable transcript found in list.")
        return None
        
    except Exception as e:
        err = str(e)
        if "Too Many Requests" in err or "429" in err or "IpBlocked" in err or "blocking requests" in err:
            raise Exception("IP_BLOCK") # Re-raise for main loop handling
        else:
            print(f"    [ERROR LOG] {type(e).__name__}: {err}")
        return None

def main():
    print("=== YouTube Transcript Downloader (Anti-Ban Enhanced) ===")
    print(f"Settings: Sleep {SLEEP_MIN}-{SLEEP_MAX}s | Batch break every {BATCH_SIZE} videos")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter Playlist URL: ").strip()

    # 1. Fetch Playlist
    print("\n[Phase 1] Fetching Playlist Structure...")
    entries = get_playlist_videos(url)
    
    if not entries:
        print("No videos found!")
        return
        
    print(f"Found {len(entries)} videos.")
    
    # 2. History Filter
    history = load_history()
    
    # --- AUTO-SAVE PLAYLIST JSON ---
    # Save the full playlist metadata for the matching script
    print("[Info] Saving playlist metadata to 'playlist.json' for future matching...")
    playlist_data = []
    for e in entries:
        # Create the format expected by match_transcripts.py
        vid_url = e.get('webpage_url')
        if not vid_url and e.get('id'):
            vid_url = f"https://www.youtube.com/watch?v={e.get('id')}"
            
        playlist_data.append({
            "Title": e.get('title', 'Unknown'),
            "Video url": vid_url
        })
        
    try:
        with open("playlist.json", "w", encoding="utf-8") as f:
            json.dump(playlist_data, f, indent=4, ensure_ascii=False)
        print("    [SUCCESS] Saved playlist.json")
    except Exception as e:
        print(f"    [WARN] Could not save playlist.json: {e}")
    # -------------------------------

    queue = [e for e in entries if e and e.get('id') and e.get('id') not in history]
    print(f"Skipping {len(history)} items. Queue: {len(queue)}")
    
    # 3. Processing
    print("\n[Phase 2] Downloading Transcripts...")
    
    success_count = 0
    fail_count = 0
    consecutive_errors = 0
    
    for idx, entry in enumerate(queue):
        video_id = entry['id']
        title = entry.get('title', 'Unknown')
        
        print(f"\n>>> [{idx+1}/{len(queue)}] {title}")
        
        # Retry loop for the same video if IP is blocked
        while True:
            try:
                transcript_data = download_transcript(video_id)
                
                if transcript_data:
                    final_name = sanitize_filename(title) + ".md"
                    output_path = os.path.join(OUTPUT_DIR, final_name)
                    
                    if transcript_to_md(transcript_data, output_path, title):
                        print(f"    [SUCCESS] Saved: {final_name}")
                        save_history(video_id)
                        success_count += 1
                        consecutive_errors = 0
                        break # Success, move to next video
                    else:
                        print("    [ERROR] Parse failed - will retry next run.")
                        fail_count += 1
                        break # Failed parse, move to next
                else:
                    # No transcript available (and no exception raised)
                    print("    [WARN] No transcript available - will retry next run.")
                    fail_count += 1
                    break # Move to next

            except Exception as e:
                err = str(e)
                if "IP_BLOCK" in err:
                    print(f"\n!!! YouTube Blocked IP !!!")
                    print(f"    Action: Entering DEEP SLEEP for 10 minutes...")
                    print(f"    Time: {time.strftime('%H:%M:%S')}")
                    time.sleep(600)  # 10 minutes
                    print("    Action: Retrying same video...")
                    continue # Retry SAME video
                else:
                    print(f"    [ERROR] Unexpected: {err} - will retry next run.")
                    fail_count += 1
                    break

        # Anti-Ban: Randomized human-like sleep
        sleep_time = random.uniform(SLEEP_MIN, SLEEP_MAX)
        sleep_time += random.uniform(-2, 2)
        sleep_time = max(SLEEP_MIN, sleep_time)
        
        print(f"    [SLEEP] {sleep_time:.1f}s")
        time.sleep(sleep_time)
        
        # Anti-Ban: Batch break
        if (idx + 1) % BATCH_SIZE == 0 and idx + 1 < len(queue):
            batch_break = random.uniform(BATCH_BREAK_MIN, BATCH_BREAK_MAX)
            print(f"\n    [BATCH BREAK] Taking {batch_break:.0f}s break after {BATCH_SIZE} videos...")
            time.sleep(batch_break)
    
    print(f"\n=== COMPLETE ===")
    print(f"Success: {success_count} | Failed/Skipped: {fail_count}")

if __name__ == "__main__":
    main()
