# Capture Pipeline v2

Drop a URL. Everything else happens automatically.

---

## THE TWO CAPTURES

### Capture #1 — `/capture [URL]` — Content Pipeline (Oak Park)
Routes social media content to the right niche (Oak Park / Brazil / UGC / News).
Updates Inspiration Library tab in Ideas & Inbox spreadsheet.

```bash
python capture.py "https://instagram.com/reel/..." --project content
```

### Capture #2 — `book capture [URL]` or `sovereign capture [URL]` — Research Pipeline
Fact-checks claims for the RECEIPTS book or SOVEREIGN political inspiration page.
Downloads, transcribes, analyzes with Claude, creates a Drive doc, updates Book Tracker.

```bash
# Book research capture
python capture.py "https://instagram.com/reel/DW3qwghAZw1/" --project book --story-id BCI-002

# Sovereign political capture
python capture.py "https://instagram.com/reel/DW7TbCdCaEy/" --project sovereign --story-id SVG-001 --notes "study format only"
```

---

## PIPELINE STEPS

```
URL → yt-dlp download → Whisper transcribe → Claude analysis → Drive doc → Sheets update → Calendar task
```

| Step | book | sovereign | content |
|------|------|-----------|---------|
| Download + Transcribe | YES | YES | YES |
| Claude analysis | Fact-check (claude-opus-4-6) | Format study (claude-opus-4-6) | Classification (claude-sonnet-4-6) |
| Drive doc | The Book folder | SOVEREIGN folder | — |
| Sheets update | Book Tracker → Stories tab | — | Ideas & Inbox → Inspiration Library |
| Calendar task | YES | YES | YES |

---

## TRIGGER FROM YOUR PHONE (GitHub Actions)

1. Open GitHub mobile app
2. Go to **priihigashi/Social-media-auto → Actions → Capture Pipeline v2**
3. Tap **Run workflow**
4. Fill in:
   - **url**: the Instagram/TikTok/YouTube URL
   - **project**: book / sovereign / content
   - **story_id**: BCI-002 (or leave blank to auto-generate)
   - **notes**: any context (optional)
5. Tap **Run**

The workflow runs on GitHub servers (~5 min). When done:
- Transcript saved as artifact (download from Actions tab)
- Drive doc created automatically
- Sheets updated
- Calendar task created for tomorrow 9am

---

## LOCAL USAGE

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env

# Run
python capture.py "URL" --project book --story-id BCI-002
python capture.py "URL" --project sovereign --story-id SVG-001
python capture.py "URL" --project content
```

---

## KEY FILES

| File | Purpose |
|------|---------|
| `capture.py` | Unified entry point — all three pipelines |
| `transcribe_reel.py` | Download + transcribe core (imported by capture.py) |
| `.github/workflows/capture_workflow.yml` | GitHub Actions trigger |
| `SKILL_capture_crazy_ideas.md` | Claude skill spec for in-chat use |
| `transcripts/` | All saved transcripts and analysis files |

---

## GITHUB SECRETS REQUIRED

Add these in: **github.com/priihigashi/Social-media-auto → Settings → Secrets → Actions**

| Secret | Value |
|--------|-------|
| `OPENAI_API_KEY` | Your OpenAI API key (for Whisper transcription) |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (for Claude analysis) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Base64-encoded service account JSON |
| `GOOGLE_SHEETS_BOOK_TRACKER_ID` | `1SeDFDisb0uNeyfyv5fCS_0x5EbkJRcFeS6CGuUmlH7c` |
| `GOOGLE_SHEETS_IDEAS_INBOX_ID` | `1IrFrCNGVIF7cvAr9cIuAXvCtUR_-eQN1mdCpHXpfbcU` |
| `GOOGLE_DRIVE_BOOK_FOLDER_ID` | `1HlY1tmUHmRZ_ZfPUzGpY_j7sHbe_OCz1` |
| `GOOGLE_DRIVE_SOVEREIGN_FOLDER_ID` | `1L89dLiVYfjNu3uz3l3S_rvZPxd2I8xjZ` |

**To encode the service account JSON:**
```bash
base64 -i credentials/service_account.json | pbcopy
# Then paste into the GOOGLE_SERVICE_ACCOUNT_JSON secret
```

**Service account email:** oak-park-sheets@website-blog-491516.iam.gserviceaccount.com
Make sure this account has Editor access to The Book and SOVEREIGN Drive folders.

---

## KEY IDs

| Resource | ID |
|----------|----|
| Book Tracker spreadsheet | `1SeDFDisb0uNeyfyv5fCS_0x5EbkJRcFeS6CGuUmlH7c` |
| Ideas & Inbox spreadsheet | `1IrFrCNGVIF7cvAr9cIuAXvCtUR_-eQN1mdCpHXpfbcU` |
| The Book Drive folder | `1HlY1tmUHmRZ_ZfPUzGpY_j7sHbe_OCz1` |
| SOVEREIGN Drive folder | `1L89dLiVYfjNu3uz3l3S_rvZPxd2I8xjZ` |
| Big Crazy Ideas Drive folder | `15iwAO8NskHDcjVn87z_zG0E3SzSdzqCW` |
| Book Promo spreadsheet | `1gCdPrFV8_lvmbrIBkQnWxyldzswB8SgodhvNpyBQmSI` |

---

## STORY ID FORMAT

- Book stories: `BCI-001`, `BCI-002`, `BCI-003`...
- SOVEREIGN stories: `SVG-001`, `SVG-002`, `SVG-003`...
- Content captures: auto-generated as `CNT-YYYYMMDDHHMM`

---

## PENDING REELS (as of 2026-04-10)

| Story ID | URL | Notes | Status |
|----------|-----|-------|--------|
| BCI-001 | instagram.com/reel/DWj0pUlEa3m/ | Trump pardons | DONE |
| BCI-002 | instagram.com/reel/DW3qwghAZw1/ | Unknown topic | NEEDS RUN |
| BCI-003 | instagram.com/reel/DW9izjRApS9/ | "Harder to prove" — verify who, find the meeting | NEEDS RUN |
| SVG-001 | instagram.com/reel/DW7TbCdCaEy/ | Format study — vague content, no teaching | NEEDS RUN |
