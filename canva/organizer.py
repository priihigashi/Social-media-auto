"""
Canva folder organizer.

Three target folders:
  1. Social Media Templates  – posts, stories, reels, thumbnails, ads
  2. Cards & Print / Flyers  – business cards, flyers, posters, brochures, menus…
  3. Starred Favorites        – designs the user has starred / saved as favourite

Categorization is done by matching the design's `design_type.name` (returned by
the Canva API) against keyword lists.  Unmatched designs are left where they are.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from canva.client import CanvaClient

# ── Keyword maps ─────────────────────────────────────────────────────────────

SOCIAL_KEYWORDS = [
    "instagram",
    "facebook",
    "twitter",
    "linkedin",
    "tiktok",
    "pinterest",
    "youtube",
    "snapchat",
    "social media",
    "social post",
    "story",
    "stories",
    "reel",
    "short",
    "thumbnail",
    "cover photo",
    "profile picture",
    "banner",
    "ad ",
    "advertisement",
]

PRINT_KEYWORDS = [
    "flyer",
    "poster",
    "business card",
    "card",
    "brochure",
    "invitation",
    "invite",
    "postcard",
    "label",
    "sticker",
    "certificate",
    "menu",
    "letterhead",
    "resume",
    "cv ",
    "a4",
    "a5",
    "letter ",
    "print",
    "booklet",
    "catalog",
    "catalogue",
    "badge",
    "ticket",
]


def _matches(type_name: str, keywords: list[str]) -> bool:
    lower = type_name.lower()
    return any(kw in lower for kw in keywords)


def categorize(design: dict) -> str | None:
    """
    Return 'social', 'print', 'starred', or None (skip / unknown).

    Priority: starred > print > social
    (A starred flyer ends up in Starred Favorites.)
    """
    # Starred / favourited designs have a `star` field set to True
    if design.get("starred") or design.get("is_starred") or design.get("favorite"):
        return "starred"

    type_name: str = (
        design.get("design_type", {}).get("name", "")
        or design.get("design_type", {}).get("type", "")
    )

    if _matches(type_name, PRINT_KEYWORDS):
        return "print"
    if _matches(type_name, SOCIAL_KEYWORDS):
        return "social"

    return None  # leave unmatched designs untouched


# ── Folder names ─────────────────────────────────────────────────────────────

FOLDER_NAMES = {
    "social": "Social Media Templates",
    "print": "Cards & Print / Flyers",
    "starred": "Starred Favorites",
}


@dataclass
class OrganizeResult:
    folders_created: list[str] = field(default_factory=list)
    moved: dict[str, int] = field(default_factory=lambda: {"social": 0, "print": 0, "starred": 0})
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def organize(client: CanvaClient, dry_run: bool = False) -> OrganizeResult:
    """
    Main entry point.

    1. Fetch all owned designs.
    2. Create the three target folders (if they don't exist yet).
    3. Move each design to its folder.

    Set dry_run=True to preview actions without making any changes.
    """
    result = OrganizeResult()

    print("Fetching your designs from Canva…")
    designs = client.list_designs(ownership="owned")
    print(f"  Found {len(designs)} designs.\n")

    # ── Create folders ────────────────────────────────────────────────────────
    folder_ids: dict[str, str] = {}
    for key, name in FOLDER_NAMES.items():
        if dry_run:
            print(f"[dry-run] Would create folder: '{name}'")
            folder_ids[key] = f"dry-run-{key}"
        else:
            print(f"Creating folder '{name}'…")
            folder = client.create_folder(name)
            folder_ids[key] = folder["id"]
            result.folders_created.append(name)
            print(f"  ✓ Created (id={folder['id']})")

    print()

    # ── Categorize & move ─────────────────────────────────────────────────────
    for design in designs:
        design_id: str = design.get("id", "")
        design_name: str = design.get("title", design_id)
        category = categorize(design)

        if category is None:
            result.skipped += 1
            continue

        folder_id = folder_ids[category]
        folder_label = FOLDER_NAMES[category]

        if dry_run:
            print(f"[dry-run] Would move '{design_name}' → '{folder_label}'")
        else:
            try:
                client.move_to_folder(folder_id, design_id)
                result.moved[category] += 1
                print(f"  Moved '{design_name}' → '{folder_label}'")
            except Exception as exc:  # noqa: BLE001
                msg = f"Failed to move '{design_name}': {exc}"
                result.errors.append(msg)
                print(f"  ✗ {msg}")

    return result
