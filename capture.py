#!/usr/bin/env python3
"""
capture.py
==========
Unified capture entry point for the content + research pipeline.

USAGE:
    # Book research (fact-check mode) — creates BCI story doc in Drive
    python capture.py "https://instagram.com/reel/DW3qwghAZw1/" --project book --story-id BCI-002

    # Sovereign political capture — creates SVG doc in SOVEREIGN Drive folder
    python capture.py "https://instagram.com/reel/DW7TbCdCaEy/" --project sovereign --story-id SVG-001

    # Oak Park content capture — classifies and routes to Inspiration Library
    python capture.py "https://instagram.com/reel/..." --project content

WHAT IT DOES:
    1. Downloads audio via yt-dlp
    2. Transcribes via OpenAI Whisper API (whisper-1)
    3. Saves transcript to /transcripts/
    4. Routes based on --project:
       book      → Claude fact-checks → BCI story doc in Drive → Book Tracker Stories tab → Calendar task
       sovereign → Claude analyses  → SVG doc in SOVEREIGN Drive folder → Calendar task
       content   → Claude classifies → Inspiration Library tab → Calendar task
"""

import os
import sys
import json
import re
import argparse
import tempfile
import base64
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import shared download/transcribe/save from transcribe_reel
from transcribe_reel import download_audio, transcribe_audio, save_transcript

# ─── CONFIG ───────────────────────────────────────────────────────────────────

OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")

# Spreadsheet IDs
BOOK_TRACKER_ID    = os.getenv("GOOGLE_SHEETS_BOOK_TRACKER_ID", "1SeDFDisb0uNeyfyv5fCS_0x5EbkJRcFeS6CGuUmlH7c")
IDEAS_INBOX_ID     = os.getenv("GOOGLE_SHEETS_IDEAS_INBOX_ID",  "1IrFrCNGVIF7cvAr9cIuAXvCtUR_-eQN1mdCpHXpfbcU")

# Drive folder IDs
BOOK_FOLDER_ID      = os.getenv("GOOGLE_DRIVE_BOOK_FOLDER_ID",      "1HlY1tmUHmRZ_ZfPUzGpY_j7sHbe_OCz1")
SOVEREIGN_FOLDER_ID = os.getenv("GOOGLE_DRIVE_SOVEREIGN_FOLDER_ID", "1L89dLiVYfjNu3uz3l3S_rvZPxd2I8xjZ")

TRANSCRIPTS_DIR = Path(__file__).parent / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)


# ─── GOOGLE AUTH ──────────────────────────────────────────────────────────────

def _get_creds(scopes: list):
    """Return Google credentials from env (GitHub Actions) or local file."""
    from google.oauth2.service_account import Credentials

    sa_b64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_b64:
        sa_info = json.loads(base64.b64decode(sa_b64))
        return Credentials.from_service_account_info(sa_info, scopes=scopes)

    creds_path = Path(__file__).parent / "credentials" / "service_account.json"
    if creds_path.exists():
        return Credentials.from_service_account_file(str(creds_path), scopes=scopes)

    raise RuntimeError(
        "No Google credentials found. "
        "Set GOOGLE_SERVICE_ACCOUNT_JSON env var or add credentials/service_account.json"
    )


def get_sheets_client():
    """Return authorized gspread client."""
    try:
        import gspread
    except ImportError:
        print("  SKIP: gspread not installed. Run: pip install gspread")
        return None
    try:
        creds = _get_creds(["https://www.googleapis.com/auth/spreadsheets"])
        return gspread.authorize(creds)
    except Exception as e:
        print(f"  SKIP: Sheets auth failed: {e}")
        return None


def get_drive_service():
    """Return authorized Google Drive v3 service."""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("  SKIP: google-api-python-client not installed.")
        return None
    try:
        creds = _get_creds([
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/documents",
        ])
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        print(f"  SKIP: Drive auth failed: {e}")
        return None


def get_docs_service():
    """Return authorized Google Docs v1 service."""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        return None
    try:
        creds = _get_creds(["https://www.googleapis.com/auth/documents"])
        return build("docs", "v1", credentials=creds)
    except Exception as e:
        print(f"  SKIP: Docs auth failed: {e}")
        return None


def get_calendar_service():
    """Return authorized Google Calendar v3 service."""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        return None
    try:
        creds = _get_creds(["https://www.googleapis.com/auth/calendar"])
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        print(f"  SKIP: Calendar auth failed: {e}")
        return None


# ─── CLAUDE ANALYSIS ──────────────────────────────────────────────────────────

def analyze_book(transcript: str, url: str, story_id: str, notes: str) -> str:
    """Run Claude capture_crazy_ideas skill for book research capture."""
    if not ANTHROPIC_API_KEY:
        print("  WARNING: ANTHROPIC_API_KEY not set — returning raw transcript")
        return f"[ANALYSIS PENDING — ANTHROPIC_API_KEY required]\n\nTRANSCRIPT:\n{transcript}"

    try:
        import anthropic
    except ImportError:
        print("  SKIP: anthropic not installed. Run: pip install anthropic")
        return transcript

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    print("  Sending to Claude (claude-opus-4-6) for fact-check analysis...")

    prompt = f"""You are running the capture_crazy_ideas skill for the RECEIPTS book project.

Story ID: {story_id}
Source URL: {url}
Notes: {notes or "None"}
Date: {datetime.now().strftime("%Y-%m-%d")}

TRANSCRIPT:
---
{transcript}
---

Produce a complete STORY DOCUMENT using this EXACT format (no markdown tables):

STORY ID: {story_id}
BOOK SECTION: [Trump Pardons | Political Deals | Historical Context | Other]
DATE CAPTURED: {datetime.now().strftime("%Y-%m-%d")}
SOURCE URL: {url}
TRANSCRIPT: [paste full transcript above]

SPEAKER: [full name, title, affiliation]
CREDENTIALS: [what makes them credible or not]
CREDIBILITY: HIGH / MEDIUM / LOW / UNVERIFIED

BACKGROUND (plain English, 8th grade level, 2-3 paragraphs):
[Who is this person? What did they do? Why does it matter?]

CLAIMS MADE:

  Claim 1: [exact quote or paraphrase]
  Fact Check: TRUE / FALSE / PARTIALLY TRUE / UNVERIFIED
  Evidence: [what we found]
  Official Sources: [URL1] | [URL2] | [URL3]

  [Add Claim 2, Claim 3 etc as needed]

SPEAKER VERIFICATION:
  Full name: [name]
  Title and affiliation: [details]
  Platform following: [if known]
  Red flags: [vague claims? no sources? inconsistencies?]
  Credibility rating: HIGH / MEDIUM / LOW / UNVERIFIED

MEETING VERIFICATION (if any meeting is claimed):
  Meeting claimed: YES [describe] / NO
  Evidence found: [URL or "No corroborating evidence found"]
  Official confirmation: [did any official confirm or deny this?]

PRESIDENTIAL / OFFICIAL STATEMENTS:
  [Did any president, senator, DOJ official, or court confirm or deny the claims?]
  [Quote with source URL. If none found, write: "No official statement found."]

PATTERN / CONNECTION:
  [Did anything happen before or after this that seems related?]
  [Donations? Deals? Visits? Business connections? Timing?]
  [PATTERN - investigate further] or [No pattern found yet]

VISUAL SUGGESTIONS:
  - [Image or screenshot idea 1 that would support this claim in the book]
  - [Image or screenshot idea 2]
  - [Image or screenshot idea 3]

SOVEREIGN POST ANGLE:
  Hook: [opening line that would stop the scroll]
  Core message: [what SOVEREIGN would say with examples, not just negatives]
  Format: [talking head / carousel / before-after / text overlay]
  Emotion: [anger / inspiration / outrage / other]

PORTUGUESE ANGLE:
  Relevant to Brazilian audience: YES / NO
  Why: [one sentence explanation]
  PT-BR hook: [if YES, write the hook in Portuguese]

QR CODE SOURCES (for printed book):
  1. [Source name] - [URL]
  2. [Source name] - [URL]
  3. [Source name] - [URL]

BOOK READY: YES / NO / NEEDS MORE RESEARCH"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def analyze_sovereign(transcript: str, url: str, story_id: str, notes: str) -> str:
    """Run Claude analysis for SOVEREIGN political inspiration capture."""
    if not ANTHROPIC_API_KEY:
        return f"[ANALYSIS PENDING — ANTHROPIC_API_KEY required]\n\nTRANSCRIPT:\n{transcript}"

    try:
        import anthropic
    except ImportError:
        return transcript

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    print("  Sending to Claude (claude-opus-4-6) for SOVEREIGN analysis...")

    prompt = f"""You are creating a content analysis for the SOVEREIGN political inspiration page.
Study the format and do it better — more concrete examples, more teaching, not just negatives.

Story ID: {story_id}
Source URL: {url}
Notes: {notes or "None"}
Date: {datetime.now().strftime("%Y-%m-%d")}

TRANSCRIPT:
---
{transcript}
---

Produce a SOVEREIGN CAPTURE DOCUMENT:

STORY ID: {story_id}
PROJECT: SOVEREIGN
DATE CAPTURED: {datetime.now().strftime("%Y-%m-%d")}
SOURCE URL: {url}

SPEAKER ANALYSIS:
  Who: [name, title, platform and following]
  Credibility: HIGH / MEDIUM / LOW / UNVERIFIED
  Red flags: [vague? no sources? only negatives? no actionable content?]

CONTENT ANALYSIS:
  Main message: [one sentence]
  Emotional tone: [anger / fear / inspiration / outrage / other]
  What works: [specific format strengths]
  What's missing: [what they fail to do — e.g. no examples, no solutions, only complaints]

SOVEREIGN POST ANGLE:
  Hook: [opening line that stops the scroll]
  Core message: [what SOVEREIGN says differently — with concrete examples]
  Teaching moment: [what the audience actually learns and can apply]
  Format: [talking head / carousel / before-after / text overlay]
  CTA: [what action do we want the audience to take]

PORTUGUESE ANGLE:
  Relevant to Brazilian audience: YES / NO
  PT-BR hook: [if YES, write the hook in Portuguese]

STUDY NOTES (3 specific ways to do it better):
  1. [Specific improvement]
  2. [Specific improvement]
  3. [Specific improvement]

CONTENT READY: YES / NO / NEEDS REFINEMENT"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def analyze_content(transcript: str, url: str, notes: str) -> dict:
    """Classify content for Oak Park pipeline using Claude."""
    if not ANTHROPIC_API_KEY:
        return {
            "niche": "Oak Park",
            "content_type": "Other",
            "classification": "NEEDS_REVIEW",
            "summary": transcript[:200],
            "hook": "",
            "notes": "ANTHROPIC_API_KEY not set"
        }

    try:
        import anthropic
    except ImportError:
        return {"niche": "Oak Park", "classification": "NEEDS_REVIEW", "summary": transcript[:200]}

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    print("  Sending to Claude (claude-sonnet-4-6) for content classification...")

    prompt = f"""Classify this video transcript for the Oak Park Construction content pipeline.

Source URL: {url}
Notes: {notes or "None"}

TRANSCRIPT:
---
{transcript}
---

Respond with a JSON object only (no other text):
{{
  "niche": "Oak Park" or "Brazil" or "UGC" or "News",
  "content_type": "Talking Head/Expert" or "Project Progress/Before-After" or "Product Tips" or "Other",
  "classification": "READY" or "NEEDS_REVIEW" or "NOT_RELEVANT",
  "summary": "One sentence summary of what the video is about",
  "hook": "Suggested hook for Oak Park Construction repost or reaction content",
  "notes": "Why you classified it this way"
}}

Niches:
- Oak Park: local construction, home improvement, contractor tips, Florida/Southwest market
- Brazil: Brazilian real estate, Portuguese-language content, Brazil market
- UGC: user-generated content suitable for repurposing
- News: industry news, trends, market updates"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "niche": "Oak Park",
        "classification": "NEEDS_REVIEW",
        "summary": text[:200],
        "notes": "JSON parse failed — manual review needed"
    }


# ─── DRIVE DOCUMENT ───────────────────────────────────────────────────────────

def create_drive_doc(title: str, content: str, folder_id: str) -> str:
    """Create a Google Doc in the specified shared Drive folder. Returns the doc URL."""
    drive = get_drive_service()
    if not drive:
        print("  SKIP: Drive unavailable — doc not created")
        return ""

    try:
        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
            "parents": [folder_id],
        }
        file = drive.files().create(
            body=file_metadata,
            supportsAllDrives=True,
            fields="id,webViewLink"
        ).execute()

        file_id = file.get("id")
        doc_url = file.get("webViewLink", f"https://docs.google.com/document/d/{file_id}/edit")
        print(f"  Drive doc created: {doc_url}")

        # Write content via Docs API
        docs = get_docs_service()
        if docs and content:
            try:
                docs.documents().batchUpdate(
                    documentId=file_id,
                    body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]}
                ).execute()
            except Exception as e:
                print(f"  WARNING: Doc content write failed: {e}")

        return doc_url

    except Exception as e:
        print(f"  WARNING: Drive doc creation failed: {e}")
        return ""


# ─── SHEETS ───────────────────────────────────────────────────────────────────

def update_book_tracker_stories(
    story_id: str, project: str, url: str, transcript: str,
    doc_url: str, analysis: str, notes: str
) -> None:
    """Add a row to the Book Tracker Stories tab and mark Inbox as CAPTURED."""
    gc = get_sheets_client()
    if not gc:
        return

    try:
        sh = gc.open_by_key(BOOK_TRACKER_ID)
        stories = sh.worksheet("Stories")

        summary = analysis[:150].replace("\n", " ") if analysis else ""
        book_section = "Other"
        for section in ["Trump Pardons", "Political Deals", "Historical Context"]:
            if section in analysis:
                book_section = section
                break

        row = [
            story_id,
            book_section,
            "",           # Subject — filled from Drive doc
            summary,
            url,
            "NEEDS REVIEW",
            notes or "",
            "", "", "",   # Source URLs 1-3
            "",           # Pattern_Notes
            datetime.now().strftime("%Y-%m-%d"),
            url,
            doc_url,
            "NO",         # Book_Ready
        ]
        stories.append_row(row)
        print(f"  Stories tab updated: {story_id}")

        # Mark Inbox row as CAPTURED
        try:
            inbox = sh.worksheet("Inbox")
            all_vals = inbox.get_all_values()
            clean_url = url.split("?")[0]
            for i, row_data in enumerate(all_vals):
                if clean_url in str(row_data):
                    inbox.update_cell(i + 1, 4, story_id)
                    inbox.update_cell(i + 1, 5, f"CAPTURED — {datetime.now().strftime('%Y-%m-%d')}")
                    break
        except Exception:
            pass

    except Exception as e:
        print(f"  WARNING: Book Tracker update failed: {e}")


def update_inspiration_library(url: str, transcript: str, classification: dict) -> None:
    """Add a row to the Inspiration Library tab in Ideas & Inbox."""
    gc = get_sheets_client()
    if not gc:
        return

    try:
        sh = gc.open_by_key(IDEAS_INBOX_ID)
        lib = sh.worksheet("Inspiration Library")

        row = [
            datetime.now().strftime("%Y-%m-%d"),
            url,
            classification.get("summary", ""),
            classification.get("niche", "Oak Park"),
            classification.get("content_type", ""),
            classification.get("classification", "NEEDS_REVIEW"),
            transcript[:300] if transcript else "",
            classification.get("hook", ""),
            classification.get("notes", ""),
        ]
        lib.append_row(row)
        print(f"  Inspiration Library updated")

    except Exception as e:
        print(f"  WARNING: Inspiration Library update failed: {e}")


# ─── CALENDAR ─────────────────────────────────────────────────────────────────

def create_calendar_task(
    story_id: str, project: str, url: str, doc_url: str,
    transcript_preview: str, notes: str
) -> None:
    """Create a Google Calendar review task for tomorrow 9am ET."""
    cal = get_calendar_service()
    if not cal:
        print("  SKIP: Calendar service unavailable")
        return

    labels = {
        "book":      "📚 BOOK CAPTURE",
        "sovereign": "👑 SOVEREIGN CAPTURE",
        "content":   "📱 CONTENT CAPTURE",
    }
    label = labels.get(project, "CAPTURE")

    description = (
        f"{label}: {story_id}\n\n"
        f"SOURCE URL: {url}\n\n"
        f"TRANSCRIPT PREVIEW:\n{transcript_preview[:500]}\n\n"
        f"DRIVE DOC: {doc_url or 'Not created — check transcripts/ folder'}\n\n"
        f"NOTES: {notes or 'None'}\n\n"
        f"NEXT STEPS:\n"
        f"1. Review the story document in Drive\n"
        f"2. Verify all sources manually\n"
        f"3. If BOOK READY: move to editing queue\n"
        f"4. Run capture again if more research needed"
    )

    tomorrow = (datetime.now() + timedelta(days=1)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    event = {
        "summary": f"{label} — {story_id} — Review Required",
        "description": description,
        "start": {"dateTime": tomorrow.isoformat(), "timeZone": "America/New_York"},
        "end":   {"dateTime": (tomorrow + timedelta(hours=1)).isoformat(), "timeZone": "America/New_York"},
    }

    try:
        cal.events().insert(calendarId="primary", body=event).execute()
        print(f"  Calendar task created for {story_id} — tomorrow 9am ET")
    except Exception as e:
        print(f"  WARNING: Calendar task failed: {e}")


# ─── PROJECT PIPELINES ────────────────────────────────────────────────────────

def run_book(args, transcript: str) -> None:
    print("\n[BOOK MODE] Running capture_crazy_ideas pipeline...")

    print("\n[ANALYZE] Running Claude fact-check analysis...")
    analysis = analyze_book(transcript, args.url, args.story_id, args.notes or "")

    analysis_path = TRANSCRIPTS_DIR / f"{args.story_id}_analysis.txt"
    with open(analysis_path, "w", encoding="utf-8") as f:
        f.write(analysis)
    print(f"  Analysis saved locally: {analysis_path}")

    print("\n[DRIVE] Creating story document in The Book folder...")
    doc_title = f"{args.story_id} — {datetime.now().strftime('%Y-%m-%d')}"
    doc_url = create_drive_doc(doc_title, analysis, BOOK_FOLDER_ID)

    print("\n[SHEETS] Updating Book Tracker...")
    update_book_tracker_stories(
        args.story_id, args.project, args.url, transcript,
        doc_url, analysis, args.notes or ""
    )

    print("\n[CALENDAR] Creating review task...")
    create_calendar_task(
        args.story_id, args.project, args.url, doc_url,
        transcript[:500], args.notes or ""
    )

    print(f"\n{'='*60}")
    print(f"BOOK CAPTURE COMPLETE")
    print(f"  Story ID:   {args.story_id}")
    print(f"  Drive doc:  {doc_url or 'check transcripts/ folder'}")
    print(f"  Local file: {analysis_path}")
    print(f"{'='*60}")


def run_sovereign(args, transcript: str) -> None:
    print("\n[SOVEREIGN MODE] Running SOVEREIGN analysis pipeline...")

    print("\n[ANALYZE] Running Claude SOVEREIGN analysis...")
    analysis = analyze_sovereign(transcript, args.url, args.story_id, args.notes or "")

    analysis_path = TRANSCRIPTS_DIR / f"{args.story_id}_sovereign_analysis.txt"
    with open(analysis_path, "w", encoding="utf-8") as f:
        f.write(analysis)
    print(f"  Analysis saved locally: {analysis_path}")

    print("\n[DRIVE] Creating doc in SOVEREIGN folder...")
    doc_title = f"{args.story_id} — SOVEREIGN — {datetime.now().strftime('%Y-%m-%d')}"
    doc_url = create_drive_doc(doc_title, analysis, SOVEREIGN_FOLDER_ID)

    print("\n[CALENDAR] Creating review task...")
    create_calendar_task(
        args.story_id, args.project, args.url, doc_url,
        transcript[:500], args.notes or ""
    )

    print(f"\n{'='*60}")
    print(f"SOVEREIGN CAPTURE COMPLETE")
    print(f"  Story ID:   {args.story_id}")
    print(f"  Drive doc:  {doc_url or 'check transcripts/ folder'}")
    print(f"  Local file: {analysis_path}")
    print(f"{'='*60}")


def run_content(args, transcript: str) -> None:
    print("\n[CONTENT MODE] Running content classification pipeline...")

    print("\n[CLASSIFY] Running Claude classification...")
    classification = analyze_content(transcript, args.url, args.notes or "")

    story_id = args.story_id or f"CNT-{datetime.now().strftime('%Y%m%d%H%M')}"

    print("\n[SHEETS] Updating Inspiration Library...")
    update_inspiration_library(args.url, transcript, classification)

    print("\n[CALENDAR] Creating review task...")
    create_calendar_task(
        story_id, args.project, args.url, "",
        transcript[:500], args.notes or ""
    )

    print(f"\n{'='*60}")
    print(f"CONTENT CAPTURE COMPLETE")
    print(f"  Niche:    {classification.get('niche', 'Unknown')}")
    print(f"  Type:     {classification.get('content_type', 'Unknown')}")
    print(f"  Status:   {classification.get('classification', 'Unknown')}")
    print(f"  Summary:  {classification.get('summary', '')}")
    print(f"{'='*60}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Capture Pipeline v2 — book, sovereign, or content"
    )
    parser.add_argument("url", help="Instagram / TikTok / YouTube URL")
    parser.add_argument(
        "--project",
        choices=["book", "sovereign", "content"],
        default="book",
        help="Pipeline to run (default: book)"
    )
    parser.add_argument(
        "--story-id",
        default=None,
        help="Story ID e.g. BCI-002 or SVG-001. Auto-generated if omitted."
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Additional context or notes for this capture"
    )
    args = parser.parse_args()

    # Auto-generate story ID if not provided
    if not args.story_id:
        prefix = {"book": "BCI", "sovereign": "SVG", "content": "CNT"}[args.project]
        args.story_id = f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M')}"

    print("\n" + "=" * 60)
    print("CAPTURE PIPELINE v2")
    print("=" * 60)
    print(f"URL:      {args.url}")
    print(f"Project:  {args.project.upper()}")
    print(f"Story ID: {args.story_id}")
    print(f"Notes:    {args.notes or 'None'}")
    print("=" * 60)

    # Step 1-3: Download → Transcribe → Save
    with tempfile.TemporaryDirectory() as tmp_dir:
        audio_path = download_audio(args.url, tmp_dir)
        transcript = transcribe_audio(audio_path)
        save_transcript(transcript, args.url, args.story_id, args.project)

    # Route based on project
    if args.project == "book":
        run_book(args, transcript)
    elif args.project == "sovereign":
        run_sovereign(args, transcript)
    elif args.project == "content":
        run_content(args, transcript)


if __name__ == "__main__":
    main()
