"""Step 4 — Output & Logging.

Prints the session summary and marks the processed row as Done.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import gspread

from sheets.client import mark_done


def log_session(
    ws: gspread.Worksheet,
    row_num: int,
    video: dict,
    finished_clips: list[Path],
    output_dir: Path,
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    mark_done(ws, row_num, timestamp)

    print()
    print("=" * 60)
    print("SESSION SUMMARY")
    print("=" * 60)
    print(f"  Source   : {video['title']}")
    print(f"  URL      : {video['url']}")
    print(f"  Channel  : {video['channel']}")
    print(f"  Output   : {output_dir}")
    print(f"  Clips    : {len(finished_clips)}")
    for clip in finished_clips:
        size_mb = clip.stat().st_size / 1_048_576
        print(f"    • {clip.name}  ({size_mb:.1f} MB)")
    print(f"  Logged   : {timestamp}")
    print("=" * 60)
