import json
import os
import re

# Configuration - Uses relative paths from the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPT_DIR = os.path.join(SCRIPT_DIR, "transcripts")
JSON_PATH = os.path.join(SCRIPT_DIR, "playlist.json")  # Rename your JSON to this or change this name
OUTPUT_MISSING_JSON = os.path.join(SCRIPT_DIR, "missing_videos.json")
OUTPUT_FILE_LIST = os.path.join(SCRIPT_DIR, "downloaded_file_list.txt")

def normalize_title_for_filename(title):
    """
    Normalizes the JSON title to match the filename convention observed.
    Replaces " | " with "  ".
    Removes potentially problematic characters if necessary, but starting with simple replacement.
    strips trailing whitespace.
    """
    # Based on user observation: "Sözleşme İmzalıyoruz! | 0.Gün..." -> "Sözleşme İmzalıyoruz!  0.Gün..."
    normalized = title.replace(" | ", "  ")
    
    # Windows filenames can't contain certain characters. 
    # It seems the downloader might be just using the title directly but maybe sanitizing some chars.
    # Looking at the file list:
    # "1.Değerlendirme Denemesi Çözümleri | 70 Günde TYT Matematik Kampı | 2025" -> "1.Değerlendirme Denemesi Çözümleri  70 Günde TYT Matematik Kampı  2025.md"
    # So " | " becomes "  ".
    
    return normalized.strip()

def main():
    print(f"Reading transcripts from: {TRANSCRIPT_DIR}")
    try:
        files = os.listdir(TRANSCRIPT_DIR)
        # Filter for .md files and remove extension for comparison
        downloaded_titles = set()
        file_list_content = []
        
        for f in files:
            if f.endswith(".md"):
                file_list_content.append(f)
                # Remove extension
                title_without_ext = f[:-3] 
                downloaded_titles.add(title_without_ext)
                
        print(f"Found {len(downloaded_titles)} unique transcript files.")
        
        # Write list of files
        with open(OUTPUT_FILE_LIST, "w", encoding="utf-8") as f:
            for filename in sorted(file_list_content):
                f.write(filename + "\n")
        print(f"Written file list to: {OUTPUT_FILE_LIST}")

    except Exception as e:
        print(f"Error reading transcript directory: {e}")
        return

    print(f"Reading JSON from: {JSON_PATH}")
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            video_list = json.load(f)
        print(f"Found {len(video_list)} videos in JSON.")
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    missing_videos = []
    
    # Pre-process downloaded files to extract (Day, Video) info if possible
    # Map: (day, video) -> set of filenames
    # We use a set because theoretically strict duplicates shouldn't exist but we should be careful.
    # Video can be None if not found.
    
    file_metadata = {}
    
    for fname in downloaded_titles:
        # Patter 1: Turkish "43.Gün - 1.Video" or "43.Gün"
        # Patter 2: English "Day 43 - Video 1" or "Day 43"
        
        day = None
        video_num = None
        
        # Extract Day
        day_match_tr = re.search(r'(\d+)\.Gün', fname)
        day_match_en = re.search(r'Day (\d+)', fname)
        
        if day_match_tr:
            day = int(day_match_tr.group(1))
        elif day_match_en:
            day = int(day_match_en.group(1))
            
        # Extract Video
        vid_match_tr = re.search(r'(\d+)\.Video', fname)
        vid_match_en = re.search(r'Video (\d+)', fname)
        
        if vid_match_tr:
            video_num = int(vid_match_tr.group(1))
        elif vid_match_en:
            video_num = int(vid_match_en.group(1))
            
        # Store metadata
        if day is not None:
             # Key is (day, video_num)
             # video_num can be None
             key = (day, video_num)
             if key not in file_metadata:
                 file_metadata[key] = []
             file_metadata[key].append(fname)

    # Now iterate JSON
    matched_files = set()
    
    for video in video_list:
        original_title = video.get("Title", "")
        
        # 1. Try Exact/Normalized string matching first
        found_by_name = False
        candidates = [
            original_title.replace(" | ", "  "),
            original_title.replace("|", " "),
            original_title.replace("|", ""), # Maybe it was removed?
            # Also handled "Pozitif ve Negatif Sayılar| 1.Gün" -> "Pozitif ve Negatif Sayılar 1.Gün" (space added, pipe removed)
            # The file was "Pozitif ve Negatif Sayılar 1.Gün", so " | " -> " " (one space) if strict pipe.
             original_title.replace(" | ", " ")
        ]
        
        for cand in candidates:
            if cand in downloaded_titles:
                matched_files.add(cand)
                found_by_name = True
                break
            if cand.strip() in downloaded_titles:
                matched_files.add(cand.strip())
                found_by_name = True
                break
                
        if found_by_name:
            continue
            
        # 2. Try Day/Video matching
        # Extract metadata from JSON Title
        day = None
        video_num = None
        
        day_match = re.search(r'(\d+)\.Gün', original_title)
        if day_match:
            day = int(day_match.group(1))
            
        vid_match = re.search(r'(\d+)\.Video', original_title)
        if vid_match:
            video_num = int(vid_match.group(1))
            
        if day is not None:
            key = (day, video_num)
            
            # Use fuzzy check
            # If we find files with same Day and VideoNum, matching is highly likely.
            # But what if specific videoNum is None? 
            # e.g. "Sözleşme İmzalıyoruz! | 0.Gün" -> Day 0, Video None
            
            potential_files = file_metadata.get(key)
            if potential_files:
                # We assume if we found a file with same Day/Video, it is the one.
                # Since we are just looking for "missing" ones, this is safe.
                # We mark it as found.
                # We pick the first one to add to matched_files for accounting
                matched_files.add(potential_files[0]) 
                continue
                
            # Fallback: Maybe JSON says "43.Gün - 1.Video" but file says "Day 43" (no video num)?
            # Or vice versa.
            # If JSON has video num, file SHOULD have it.
            # If file has video num, JSON SHOULD have it.
            
        # If we reached here, it is missing
        missing_videos.append(video)

    print(f"identified {len(missing_videos)} missing videos.")
    
    unmatched_files = downloaded_titles - matched_files
    print(f"Found {len(unmatched_files)} files on disk that did not match any JSON entry.")
    
    if unmatched_files:
        print("Unmatched files sample:")
        for f in list(unmatched_files)[:10]:
            print(f" - {f}")

    # Write missing videos to JSON

    # Write missing videos to JSON
    with open(OUTPUT_MISSING_JSON, "w", encoding="utf-8") as f:
        json.dump(missing_videos, f, indent=4, ensure_ascii=False)
    print(f"Written missing videos to: {OUTPUT_MISSING_JSON}")

if __name__ == "__main__":
    main()
