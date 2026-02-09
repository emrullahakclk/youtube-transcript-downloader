import json
import subprocess
import os
import sys

# Configuration - Uses relative paths from the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MISSING_JSON_PATH = os.path.join(SCRIPT_DIR, "missing_videos.json")
DOWNLOADER_SCRIPT = os.path.join(SCRIPT_DIR, "transcript_downloader.py")

def main():
    if not os.path.exists(MISSING_JSON_PATH):
        print(f"Error: {MISSING_JSON_PATH} not found.")
        return

    try:
        with open(MISSING_JSON_PATH, "r", encoding="utf-8") as f:
            missing_videos = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    if not missing_videos:
        print("No missing videos to download.")
        return

    print(f"Starting download for {len(missing_videos)} videos...")

    for i, video in enumerate(missing_videos):
        title = video.get("Title")
        url = video.get("Video url")
        
        print(f"\n--- [{i+1}/{len(missing_videos)}] Downloading: {title} ---")
        print(f"URL: {url}")
        
        try:
            # Calling the existing transcript_downloader.py as a subprocess
            # This ensures we use the anti-ban logic and settings defined there.
            result = subprocess.run([sys.executable, DOWNLOADER_SCRIPT, url], 
                                     cwd=os.path.dirname(DOWNLOADER_SCRIPT),
                                     text=True)
            
            if result.returncode == 0:
                print(f"Successfully processed: {title}")
            else:
                print(f"Warning: Downloader returned non-zero exit code for: {title}")
                
        except Exception as e:
            print(f"Error running downloader for {title}: {e}")

    print("\n--- All scheduled downloads complete ---")

if __name__ == "__main__":
    main()
