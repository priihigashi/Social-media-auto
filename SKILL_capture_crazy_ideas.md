# SKILL: Capture Crazy Ideas — v2
## For: RECEIPTS Book + SOVEREIGN Page

**Updated:** 2026-04-10  
**Trigger phrases:** `capture crazy ideas [URL]` | `book capture [URL]` | `sovereign capture [URL]`

**Spreadsheet:** Book Tracker — ID: 1SeDFDisb0uNeyfyv5fCS_0x5EbkJRcFeS6CGuUmlH7c
**Spreadsheet:** Ideas & Inbox — ID: 1IrFrCNGVIF7cvAr9cIuAXvCtUR_-eQN1mdCpHXpfbcU

**Drive folder — The Book:** 1HlY1tmUHmRZ_ZfPUzGpY_j7sHbe_OCz1
**Drive folder — SOVEREIGN:** 1L89dLiVYfjNu3uz3l3S_rvZPxd2I8xjZ
**Drive folder — Big Crazy Ideas:** 15iwAO8NskHDcjVn87z_zG0E3SzSdzqCW
**Drive folder — Book Promo:** 1gCdPrFV8_lvmbrIBkQnWxyldzswB8SgodhvNpyBQmSI

---

## TWO CAPTURES — TWO MODES

### book capture [URL]
Research capture for the RECEIPTS book (fact-checking).
Story IDs: BCI-001, BCI-002, BCI-003...
Output: Story doc in The Book folder + Book Tracker Stories tab row

### sovereign capture [URL]
Political inspiration capture for the SOVEREIGN page.
Story IDs: SVG-001, SVG-002, SVG-003...
Output: Story doc in SOVEREIGN folder + study notes on format

---

## TRANSCRIPTION — REQUIRED STEP (Claude cannot do this directly)

**For Instagram/TikTok/YouTube reels, transcription MUST happen via the pipeline:**

**Option A — GitHub Actions (phone-friendly):**
Go to: github.com/priihigashi/Social-media-auto → Actions → "Capture Pipeline v2" → Run workflow
Fill in: URL, project (book/sovereign/content), story_id, notes
Everything runs automatically: download → transcribe → analyze → Drive doc → Sheets → Calendar

**Option B — Local terminal:**
```
python capture.py "https://instagram.com/reel/..." --project book --story-id BCI-002
python capture.py "https://instagram.com/reel/..." --project sovereign --story-id SVG-001
python capture.py "https://instagram.com/reel/..." --project content
```

**Option C — Claude chat session (web articles, Twitter/X, text sources):**
Paste the text content directly into Claude. Claude will fact-check without a transcript file.
For reels: Claude will note that transcription is required and provide the command to run.

---

## ROUTING LOGIC

| Trigger | Project flag | Story prefix | Sheets tab | Drive folder | Claude model |
|---------|-------------|--------------|------------|--------------|--------------|
| book capture | --project book | BCI | Book Tracker → Stories | The Book | claude-opus-4-6 |
| sovereign capture | --project sovereign | SVG | Calendar task only | SOVEREIGN | claude-opus-4-6 |
| /capture [URL] | --project content | CNT | Ideas & Inbox → Inspiration Library | — | claude-sonnet-4-6 |

---

## STEPS (Execute In Order)

### Step 1: Get the transcript
- If URL is a reel → run pipeline (Option A or B above). Transcript saved to /transcripts/
- If URL is an article/tweet → paste the text directly
- If transcript already exists → read from /transcripts/<story_id>_transcript.txt

### Step 2: Identify the source
- Who is speaking? What platform? What is their following/reach?
- Is this a verified account or anonymous?
- Source type: Instagram reel | TikTok | YouTube | Twitter/X | News article | Podcast

### Step 3: Speaker verification
- Full name and title
- Search for their official bio, LinkedIn, Wikipedia
- What are their credentials for making this claim?
- Are they connected to the people/events they are discussing?
- Rate credibility: HIGH / MEDIUM / LOW / UNVERIFIED

### Step 4: Extract every factual claim
- List each specific claim made (not opinions, specific facts)
- Quote directly when possible, paraphrase otherwise
- Note which timestamp in the reel each claim appears at (if known)

### Step 5: Fact-check each claim
- Search DOJ, WhiteHouse.gov, justice.gov/pardon, court records
- Search Wikipedia, AP, Reuters, NYT, WaPo, ProPublica, CREW (citizensforethics.org)
- Rate each claim: TRUE / FALSE / PARTIALLY TRUE / UNVERIFIED
- Note what specifically was verified and what was not

### Step 6: Meeting verification (if any meeting is claimed)
- Did they claim a specific meeting happened?
- Search for news coverage, official statements, calendar leaks
- Did any official confirm or deny the meeting?
- Note: "No corroborating evidence found" if nothing found

### Step 7: Presidential / Official statements
- Did any president, senator, attorney general, or court confirm or deny?
- Quote with source URL and date
- Note if they were silent — silence can be significant

### Step 8: Pattern analysis
- Did anything financially relevant happen before or after this event?
- Donations to campaign? Business deals? Regulatory decisions? Pardons?
- Timing: how many days before/after?
- [PATTERN — investigate further] or [No pattern found yet]

### Step 9: Visual suggestions
- What images, screenshots, or documents would make this compelling in the book?
- Court documents? Financial records? Timeline graphics?
- What would a QR code reader see if they scanned the source?

### Step 10: SOVEREIGN angle
- How would this become a powerful SOVEREIGN post?
- What's the hook that stops the scroll?
- What concrete example could replace vague claims?
- Is there a teaching moment (not just outrage)?

### Step 11: Portuguese angle
- Would this resonate with the Brazilian audience?
- Is there a parallel in Brazilian politics or real estate?
- If YES: draft the hook in PT-BR

### Step 12: Create story document → Drive
- Create a Google Doc using the BCI template below
- Save to The Book folder (book) or SOVEREIGN folder (sovereign)

### Step 13: Update spreadsheet
- Book Tracker → Stories tab (for book and sovereign)
- Book Tracker → Inbox tab (mark as CAPTURED)
- If about a pardoned person: also add to People Pardoned tab

### Step 14: Create calendar task
- Include: source URL, Drive doc link, story ID, next steps
- Schedule for next morning at 9am ET

---

## TONE / READING LEVEL

- 8th grade reading level baseline
- No accusations — only verified facts with sources
- Use: "records show" / "according to [source]" / "court documents state"
- [UNVERIFIED — needs source] for unconfirmed claims
- [PATTERN — investigate further] for suspect timing/connections
- Explain legal terms and background context simply
- Note if content is relevant to Brazilian/Portuguese audience

---

## STORY DOCUMENT TEMPLATE (BCI format)

```
STORY ID: [BCI-XXX or SVG-XXX]
BOOK SECTION: [Trump Pardons | Political Deals | Historical Context | Other]
DATE CAPTURED: [YYYY-MM-DD]
SOURCE URL: [url]
TRANSCRIPT: [full transcript from Whisper — or paste text if not a reel]

SPEAKER: [full name, title, affiliation]
CREDENTIALS: [what makes them credible or not]
CREDIBILITY: HIGH / MEDIUM / LOW / UNVERIFIED

BACKGROUND (plain English, 8th grade level, 2-3 paragraphs):
[Who is this person? What did they do? Why does it matter?]

CLAIMS MADE:

  Claim 1: [exact quote or paraphrase]
  Fact Check: TRUE / FALSE / PARTIALLY TRUE / UNVERIFIED
  Evidence: [what we found and where]
  Official Sources: [URL1] | [URL2] | [URL3]

  Claim 2: [repeat for each claim]

SPEAKER VERIFICATION:
  Full name: [name]
  Title and affiliation: [details]
  Platform following: [if known]
  Red flags: [vague? no sources? inconsistencies?]
  Credibility rating: HIGH / MEDIUM / LOW / UNVERIFIED

MEETING VERIFICATION (if any meeting is claimed):
  Meeting claimed: YES [describe] / NO
  Evidence found: [URL or "No corroborating evidence found"]
  Official confirmation: [did any official confirm or deny?]

PRESIDENTIAL / OFFICIAL STATEMENTS:
  [Did any president, senator, DOJ official, or court confirm or deny the claims?]
  [Quote with source URL and date. If none found: "No official statement found."]

PATTERN / CONNECTION:
  [Did anything happen before or after this event that seems related?]
  [Donations? Deals? Visits? Business connections? Timing in days?]
  [PATTERN — investigate further] or [No pattern found yet]

VISUAL SUGGESTIONS:
  - [Image or screenshot idea 1 for the book]
  - [Image or screenshot idea 2]
  - [Document or record that would make this visual]

SOVEREIGN POST ANGLE:
  Hook: [opening line that stops the scroll]
  Core message: [what SOVEREIGN says — with concrete examples, not just negatives]
  Teaching moment: [what the audience actually learns and can apply]
  Format: [talking head / carousel / before-after / text overlay]
  Emotion: [anger / inspiration / outrage / other]

PORTUGUESE ANGLE:
  Relevant to Brazilian audience: YES / NO
  Why: [one sentence]
  PT-BR hook: [if YES, write the hook in Portuguese]

QR CODE SOURCES (for printed book):
  1. [Source name] - [URL]
  2. [Source name] - [URL]
  3. [Source name] - [URL]

BOOK READY: YES / NO / NEEDS MORE RESEARCH
```

---

## SPREADSHEET STRUCTURE

### Book Tracker — ID: 1SeDFDisb0uNeyfyv5fCS_0x5EbkJRcFeS6CGuUmlH7c

Tab: Stories
Story_ID | Book_Section | Subject | Claim_Summary | Claim_Source_URL | Fact_Check_Status | Fact_Check_Notes | Source_1_URL | Source_2_URL | Source_3_URL | Pattern_Notes | Date_Captured | Original_URL | Document_Link | Book_Ready

Tab: People Pardoned
Person | Pardon_Date | Original_Crime | Sentence | Time_Served | Trump_Stated_Reason | WhiteHouse_URL | Donations_Or_Connections | What_Happened_After | Suspicious_Patterns | Story_ID

Tab: Sources Library
Source_ID | Title | URL | Publication | Date_Published | Archived | Screenshot_Taken | Notes | Used_In_Story_IDs

Tab: Inbox (Raw Captures)
Date | URL | Notes | Assigned_To_Story | Status

Tab: Book Outline
Section | Chapter | Title | Summary | Stories_Included | Status | Word_Count_Est

---

## THE 4 PENDING REELS — STATUS AS OF 2026-04-10

BCI-001 | https://www.instagram.com/reel/DWj0pUlEa3m/ | Trump pardons — DONE, story doc exists | COMPLETE
BCI-002 | https://www.instagram.com/reel/DW3qwghAZw1/ | Unknown topic — NEEDS transcription | PENDING
BCI-003 | https://www.instagram.com/reel/DW9izjRApS9/ | "Harder to prove" — verify speaker, find the meeting, check if presidents commented | PENDING
SVG-001 | https://www.instagram.com/reel/DW7TbCdCaEy/ | Content inspiration — vague, only negatives, no teaching. Study format, do better | PENDING

To process these: run the GitHub Actions workflow for each URL, or run locally:
python capture.py "https://www.instagram.com/reel/DW3qwghAZw1/" --project book --story-id BCI-002
python capture.py "https://www.instagram.com/reel/DW9izjRApS9/" --project book --story-id BCI-003 --notes "verify who this is, find the meeting, check presidential comments"
python capture.py "https://www.instagram.com/reel/DW7TbCdCaEy/" --project sovereign --story-id SVG-001 --notes "content inspiration — study format and do better with concrete examples"

---

## BOOK TITLE OPTIONS (pick one)
1. Fact Check This
2. Receipts: A People's Fact-Check
3. Show Your Work: The Paper Trail
4. Don't Trust Me, Check It

---

## AGENT VS SKILL NOTE
This is a SKILL (one-shot execution per trigger).
Future upgrade: agent that monitors scraping targets for pardon/political news and auto-captures.

Story ID format:
- Book stories: BCI-001, BCI-002, BCI-003...
- SOVEREIGN stories: SVG-001, SVG-002, SVG-003...
- Content captures: CNT-YYYYMMDDHHMM (auto-generated)
