#!/usr/bin/env python3
"""Video Curation & Editing Pipeline — CLI entrypoint.

Usage
─────
# Step 1: Pull trending videos into the sheet
python main.py collect

# Step 2+3+4: Process the next Pending row automatically
python main.py clip

# Step 2+3+4: Process a specific YouTube URL
python main.py clip --url https://www.youtube.com/watch?v=XXXXXXXXXXX

# Run both in sequence (collect then clip)
python main.py run
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import config
from pipeline import collector, clipper, renderer
from pipeline.logger import log_session
from sheets.client import get_sheet, next_pending


def cmd_collect(args: argparse.Namespace) -> None:
    collector.run(
        niche=args.niche or None,
        max_results=args.max_results or None,
    )


def cmd_clip(args: argparse.Namespace) -> None:
    ws = get_sheet()

    if args.url:
        # Manual URL provided — use a synthetic video dict
        video = {
            "title": args.url,
            "url": args.url,
            "views": "—",
            "duration": "—",
            "channel": "—",
            "publish_date": str(date.today()),
        }
        row_num = None  # won't update the sheet
    else:
        row_num, video = next_pending(ws)
        if video is None:
            print("[Clip] No Pending rows found in the sheet. Run `collect` first.")
            sys.exit(0)

    print(f"[Clip] Processing: {video['title']}")

    # Build output directory: clips/YYYY-MM-DD/
    today = str(date.today())
    output_dir = config.CLIPS_ROOT / today
    raw_dir = output_dir / "raw"

    # Step 2 — Mosaic clip extraction
    raw_clips = clipper.extract_clips(video["url"], raw_dir)

    if not raw_clips:
        print("[Clip] No clips returned by Mosaic. Exiting.")
        sys.exit(1)

    # Step 3 — FFmpeg cinematic treatment
    finished_clips = renderer.render_clips(raw_clips, output_dir)

    # Step 4 — Log & mark done
    if row_num is not None:
        log_session(ws, row_num, video, finished_clips, output_dir)
    else:
        # Still print summary even without sheet update
        print(f"\nDone! {len(finished_clips)} clips saved to {output_dir}")
        for clip in finished_clips:
            print(f"  • {clip.name}")


def cmd_run(args: argparse.Namespace) -> None:
    cmd_collect(args)
    cmd_clip(args)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Daily video curation and editing pipeline."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # collect
    p_collect = sub.add_parser("collect", help="Pull trending videos into Google Sheet")
    p_collect.add_argument("--niche", help="Override YOUTUBE_NICHE env var")
    p_collect.add_argument("--max-results", type=int, help="Override MAX_RESULTS env var")
    p_collect.set_defaults(func=cmd_collect)

    # clip
    p_clip = sub.add_parser("clip", help="Process next Pending row (or a specific URL)")
    p_clip.add_argument("--url", help="YouTube URL to process instead of pulling from sheet")
    p_clip.set_defaults(func=cmd_clip)

    # run (collect + clip)
    p_run = sub.add_parser("run", help="collect + clip in one shot")
    p_run.add_argument("--niche", help="Override YOUTUBE_NICHE env var")
    p_run.add_argument("--max-results", type=int)
    p_run.add_argument("--url", help="YouTube URL to process (skips sheet for clipping)")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
