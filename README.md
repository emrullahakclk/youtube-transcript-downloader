# 🎬 YouTube Transcript Downloader

A powerful Python toolkit for downloading YouTube video transcripts from playlists with anti-ban protection and intelligent matching capabilities.

## ✨ Features

- **📥 Bulk Transcript Download**: Download transcripts from entire YouTube playlists
- **🛡️ Anti-Ban Protection**: Built-in delays, randomization, and rate limit handling
- **🔄 Smart Resume**: Only successful downloads are marked as complete - failed ones automatically retry
- **📋 Auto Playlist Export**: Automatically saves playlist metadata for future reference
- **🔍 Smart Matching**: Compare downloaded files against playlist to find missing videos
- **📝 Markdown Output**: Clean, timestamped markdown files
- **🍪 Cookie Support**: Use browser cookies for age-restricted or private content

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/emrullahakclk/youtube-transcript-downloader.git
cd youtube-transcript-downloader

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```
yt-dlp
youtube-transcript-api
requests
```

## 🚀 Usage

### 1. Download Transcripts from Playlist

```bash
python transcript_downloader.py "PLAYLIST_URL"
```

Or run interactively:
```bash
python transcript_downloader.py
# Then enter the playlist URL when prompted
```

### 2. Check for Missing Transcripts

The `playlist.json` file is **automatically created** when you run the downloader. No manual setup needed!

Just run:
```bash
python match_transcripts.py
```

This will compare your downloaded files against the playlist and show any missing videos.

### 3. Download Missing Videos Only

After running `match_transcripts.py`, download only the missing ones:
```bash
python download_missing.py
```

## 📁 Project Structure

```
├── transcript_downloader.py   # Main downloader with anti-ban logic
├── match_transcripts.py       # Compare downloaded files vs playlist
├── download_missing.py        # Download only missing transcripts
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── transcripts/               # Downloaded transcripts (auto-created)
├── playlist.json              # Playlist metadata (auto-created)
├── processed_videos.txt       # History of successful downloads (auto-created)
└── cookies.txt                # Optional: Browser cookies for restricted content
```

## ⚙️ Configuration

Edit the constants at the top of `transcript_downloader.py`:

```python
SLEEP_MIN = 15          # Minimum sleep between videos (seconds)
SLEEP_MAX = 25          # Maximum sleep between videos (seconds)
BATCH_SIZE = 10         # Take longer break every N videos
BATCH_BREAK_MIN = 60    # Minimum batch break (seconds)
BATCH_BREAK_MAX = 120   # Maximum batch break (seconds)
```

## 🍪 Using Cookies (Optional)

For age-restricted or private videos, export cookies from your browser:

1. Install a browser extension like "Get cookies.txt LOCALLY"
2. Log in to YouTube
3. Export cookies to `cookies.txt` in the project directory

## 🛡️ Anti-Ban Features

This tool includes multiple anti-ban measures:

- **Random Delays**: Varies wait time between requests
- **Batch Breaks**: Takes longer pauses every N videos
- **Human-like Timing**: Micro-delays to simulate real browsing
- **IP Block Detection**: Automatically pauses for 10 minutes if blocked
- **Smart Retry**: Only successful downloads are saved to history - failed ones will be retried on next run

## 📋 Output Format

Transcripts are saved as markdown files with timestamps:

```markdown
# Video Title

[00:00] Welcome to the video...
[00:05] Today we're going to learn about...
[00:10] Let's get started with the first topic...
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Disclaimer

This tool is for personal and educational use only. Please respect YouTube's Terms of Service and the content creators' rights. Do not use this tool to violate copyright or redistribute content without permission.

## 📄 License

MIT License - feel free to use and modify as needed.
