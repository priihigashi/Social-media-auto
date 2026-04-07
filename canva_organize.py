#!/usr/bin/env python3
"""
Canva folder organizer – CLI entry point.

Usage
-----
  # Preview what would happen (no changes made):
  python canva_organize.py --dry-run

  # Run for real:
  python canva_organize.py

Requirements
------------
  Set CANVA_API_TOKEN in your .env file (or export it as an env var).
  Get your token at: https://www.canva.com/developers/

  The token needs these OAuth scopes:
    asset:read   design:content:read   design:meta:read   folder:read   folder:write
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from canva.client import CanvaClient
from canva.organizer import FOLDER_NAMES, organize


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Organize your Canva designs into three tidy folders."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without creating folders or moving designs.",
    )
    args = parser.parse_args()

    token = os.getenv("CANVA_API_TOKEN")
    if not token:
        sys.exit(
            "Error: CANVA_API_TOKEN is not set.\n"
            "Add it to your .env file or export it as an environment variable.\n"
            "Get your token at https://www.canva.com/developers/"
        )

    client = CanvaClient(token)

    print("=" * 60)
    print("  Canva Folder Organizer")
    print("=" * 60)
    if args.dry_run:
        print("  *** DRY RUN – no changes will be made ***")
    print()
    print("  Target folders:")
    for key, name in FOLDER_NAMES.items():
        print(f"    • {name}")
    print()

    result = organize(client, dry_run=args.dry_run)

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    if not args.dry_run:
        print(f"  Folders created : {len(result.folders_created)}")
        print(f"  Social Media    : {result.moved['social']} designs moved")
        print(f"  Cards & Print   : {result.moved['print']} designs moved")
        print(f"  Starred Favs    : {result.moved['starred']} designs moved")
        print(f"  Skipped (other) : {result.skipped} designs")
        if result.errors:
            print(f"\n  Errors ({len(result.errors)}):")
            for err in result.errors:
                print(f"    ✗ {err}")
    print()
    print("  Done!")


if __name__ == "__main__":
    main()
