#!/usr/bin/env python3
"""
transcribe_reel.py
==================
Capture + transcribe any Instagram (or TikTok) reel URL.

USAGE:
    python transcribe_reel.py <reel_url> [--story-id BCI-002] [--project book|sovereign|content]

EXAMPLES:
    python transcribe_reel.py "https://www.instagram.com/reel/DW3qwghAZw1/" --story-id BCI-002 --project book
    python transcribe_reel.py "https://www.instagram.com/reel/DW9izjRApS9/" --story-id BCI-003 --project book
    python transcribe_reel.py "https://www.instagram.com/reel/DW7TbCdCaEy/" --story-id SVG-001 --project sovereign

WHAT IT DOES:
    1. Downloads audio from the reel using yt-dlp
    2. Transcribes audio using OpenAI Whisper API
    3. Prints the full transcript to console
    4. Saves transcript to /transcripts/<story_id>_transcript.txt
    5. Updates the Google Sheets Book Tracker Inbox tab (status: TRANSCRIBED)
    6. Optionally triggers Claude API to run capture_crazy_ideas skill on the transcript

REQUIRED ENV VARS (add to .env):
    OPENAI_API_KEY=sk-...
    GOOGLE_SHEETS_BOOK_TRACKER_ID=1SeDFDisb0uNeyfyv5fCS_0x5EbkJRcFeS6CGuUmlH7c
    ANTHROPIC_API_KEY=sk-ant-...   (optional, for auto-capture)

DEPENDENCIES:
    pip install yt-dlp openai gspread google-auth anthropic python-dotenv
"""

import os
import sys
import json
import argparse
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ─── CONFIG ───────────────────────────────────────────────────────────────────

BOOK_TRACKER_ID = os.getenv(
    "GOOGLE_SHEETS_BOOK_TRACKER_ID",
    "1SeDFDisb0uNeyfyv5fCS_0x5EbkJRcFeS6CGuUmlH7c"
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

TRANSCRIPTS_DIR = Path(__file__).parent / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)


# ─── STEP 1: DOWNLOAD AUDIO ───────────────────────────────────────────────────

def download_audio(reel_url: str, tmp_dir: str) -> str:
    """
    Download audio from an Instagram or TikTok reel using yt-dlp.
    Returns path to the downloaded .mp3 file.
    """
    print(f"\n[1/4] Downloading audio from: {reel_url}")

    output_template = os.path.join(tmp_dir, "reel_audio.%(ext)s")

    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--output", output_template,
        "--no-playlist",
        "--quiet",
        reel_url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ERROR: yt-dlp failed: {result.stderr}")
        print("  Tip: Make sure yt-dlp is installed: pip install yt-dlp")
        print("  Tip: For private/login-required reels, add: --cookies-from-browser chrome")
        sys.exit(1)

    # Find the downloaded file
    mp3_path = os.path.join(tmp_dir, "reel_audio.mp3")
    if not os.path.exists(mp3_path):
        # Try other extensions
        for ext in ["m4a", "webm", "ogg", "wav"]:
            alt = os.path.join(tmp_dir, f"reel_audio.{ext}")
            if os.path.exists(alt):
                mp3_path = alt
                break

    if not os.path.exists(mp3_path):
        print("  ERROR: Audio file not found after download.")
        sys.exit(1)

    size_kb = os.path.getsize(mp3_path) / 1024
    print(f"  Downloaded: {mp3_path} ({size_kb:.1f} KB)")
    return mp3_path


# ─── STEP 2: TRANSCRIBE ───────────────────────────────────────────────────────

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio using OpenAI Whisper API.
    Returns the full transcript text.
    """
    print("\n[2/4] Transcribing audio with Whisper...")

    if not OPENAI_API_KEY:
        print("  ERROR: OPENAI_API_KEY not set. Add it to .env")
        sys.exit(1)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        print("  ERROR: openai package not installed. Run: pip install openai")
        sys.exit(1)

    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )

    print(f"  Transcription complete ({len(transcript)} chars)")
    return transcript


# ─── STEP 3: SAVE TRANSCRIPT ──────────────────────────────────────────────────

def save_transcript(transcript: str, reel_url: str, story_id: str, project: str) -> str:
    """
    Save transcript to /transcripts/<story_id>_transcript.txt
    Returns the file path.
    """
    print("\n[3/4] Saving transcript...")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    shortcode = reel_url.split("/reel/")[-1].split("/")[0].split("?")[0] if "/reel/" in reel_url else "unknown"

    content = f"""TRANSCRIPT
==========================================
Story ID:   {story_id}
Project:    {project}
Reel URL:   {reel_url}
Shortcode:  {shortcode}
Captured:   {timestamp}
==========================================

{transcript}
==========================================
END TRANSCRIPT
"""

    filename = f"{story_id}_{shortcode}_transcript.txt"
    filepath = TRANSCRIPTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Saved: {filepath}")
    return str(filepath)


# ─── STEP 4: UPDATE GOOGLE SHEETS ─────────────────────────────────────────────

def update_sheets_inbox(reel_url: str, story_id: str, project: str, transcript: str) -> None:
    """
    Update the Book Tracker Inbox tab to mark the reel as TRANSCRIBED.
    Requires gspread + Google service account credentials.
    """
    print("\n[4/4] Updating Google Sheets Inbox...")

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("  SKIP: gspread not installed. Run: pip install gspread google-auth")
        print("  (Sheets update skipped — transcript was saved locally)")
        return

    creds_path = Path(__file__).parent / "credentials" / "service_account.json"
    if not creds_path.exists():
        print(f"  SKIP: No credentials found at {creds_path}")
        print("  (Sheets update skipped — transcript was saved locally)")
        return

    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(BOOK_TRACKER_ID)
        inbox = sh.worksheet("Inbox")

        # Find the row with this URL
        all_values = inbox.get_all_values()
        for i, row in enumerate(all_values):
            if reel_url.split("?")[0] in str(row):
                row_num = i + 1
                # Update status column (column E = 5)
                inbox.update_cell(row_num, 5, f"TRANSCRIBED — {datetime.now().strftime('%Y-%m-%d')}")
                # Update notes column (column C = 3) with first 200 chars of transcript
                preview = transcript[:200].replace("\n", " ")
                existing_note = inbox.cell(row_num, 3).value or ""
                inbox.update_cell(row_num, 3, f"{existing_note} | TRANSCRIPT: {preview}...")
                print(f"  Updated row {row_num} in Inbox tab")
                return

        # URL not found — add new row
        inbox.append_row([
            datetime.now().strftime("%Y-%m-%d"),
            reel_url,
            f"TRANSCRIPT: {transcript[:200]}...",
            story_id,
            f"TRANSCRIBED — {datetime.now().strftime('%Y-%m-%d')}"
        ])
        print("  Added new row to Inbox tab")

    except Exception as e:
        print(f"  WARNING: Sheets update failed: {e}")
        print("  (Transcript was saved locally — Sheets update can be done manually)")


# ─── OPTIONAL: AUTO-CAPTURE VIA CLAUDE ────────────────────────────────────────

def auto_capture_with_claude(transcript: str, reel_url: str, story_id: str, project: str) -> None:
    """
    Optional: send transcript to Claude API to run capture_crazy_ideas skill.
    Requires ANTHROPIC_API_KEY in .env
    """
    if not ANTHROPIC_API_KEY:
        print("\n  [AUTO-CAPTURE] Skipped — ANTHROPIC_API_KEY not set")
        return

    print("\n  [AUTO-CAPTURE] Sending transcript to Claude for capture_crazy_ideas skill...")

    try:
        import anthropic
    except ImportError:
        print("  SKIP: anthropic package not installed. Run: pip install anthropic")
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are running the capture_crazy_ideas skill for the RECEIPTS book project.

Story ID: {story_id}
Project: {project}
Source URL: {reel_url}

Here is the transcript from the Instagram reel:

---
{transcript}
---

Please:
1. Identify every factual claim made in the transcript
2. For each claim: state what was claimed and rate if it is TRUE / FALSE / PARTIALLY TRUE / UNVERIFIED
3. Find 3 official sources for each claim (DOJ, White House, Wikipedia, AP, Reuters, NYT, Marshall Project, CREW)
4. Note any suspicious patterns (timing, donations, connections)
5. Note who the speaker is and their credibility
6. Format as a RECEIPTS book story document following the BCI-001 format

Output the complete story document."""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    auto_capture_output = message.content[0].text

    # Save to transcripts dir
    output_path = TRANSCRIPTS_DIR / f"{story_id}_auto_capture.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(auto_capture_output)

    print(f"  Auto-capture saved: {output_path}")
    print("\n" + "="*60)
    print("AUTO-CAPTURE OUTPUT:")
    print("="*60)
    print(auto_capture_output[:2000] + ("..." if len(auto_capture_output) > 2000 else ""))


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Transcribe an Instagram reel and run the capture_crazy_ideas skill"
    )
    parser.add_argument("url", help="Instagram or TikTok reel URL")
    parser.add_argument(
        "--story-id",
        default=f"BCI-{datetime.now().strftime('%Y%m%d%H%M')}",
        help="Story ID (e.g. BCI-002, SVG-001). Defaults to timestamp."
    )
    parser.add_argument(
        "--project",
        choices=["book", "sovereign", "content"],
        default="book",
        help="Which project this capture belongs to (default: book)"
    )
    parser.add_argument(
        "--auto-capture",
        action="store_true",
        help="Automatically run Claude capture_crazy_ideas skill on transcript"
    )
    args = parser.parse_args()

    print("\n" + "="*60)
    print("REEL TRANSCRIPTION PIPELINE")
    print("="*60)
    print(f"URL:       {args.url}")
    print(f"Story ID:  {args.story_id}")
    print(f"Project:   {args.project}")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Step 1: Download
        audio_path = download_audio(args.url, tmp_dir)

        # Step 2: Transcribe
        transcript = transcribe_audio(audio_path)

        # Step 3: Save
        transcript_path = save_transcript(transcript, args.url, args.story_id, args.project)

    # Step 4: Update sheets
    update_sheets_inbox(args.url, args.story_id, args.project, transcript)

    # Optional: Auto-capture
    if args.auto_capture:
        auto_capture_with_claude(transcript, args.url, args.story_id, args.project)

    # Final output
    print("\n" + "="*60)
    print("TRANSCRIPT:")
    print("="*60)
    print(transcript)
    print("="*60)
    print(f"\nDone. Transcript saved to: {transcript_path}")
    print(f"Run with --auto-capture to also generate the full story doc.")


if __name__ == "__main__":
    main()
