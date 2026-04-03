"""Step 1 — YouTube Trend Collector.

Searches YouTube for trending videos in the configured niche and appends
new results to the 'Video Vault' Google Sheet.
"""
from __future__ import annotations

import isodate
from googleapiclient.discovery import build

import config
from sheets.client import get_sheet, append_videos


def _format_duration(iso: str) -> str:
    """Convert ISO 8601 duration (PT3M42S) to MM:SS string."""
    try:
        td = isodate.parse_duration(iso)
        total_seconds = int(td.total_seconds())
        return f"{total_seconds // 60}:{total_seconds % 60:02d}"
    except Exception:
        return iso


def fetch_trending_videos(niche: str | None = None, max_results: int | None = None) -> list[dict]:
    """Query YouTube Data API and return structured video metadata."""
    niche = niche or config.YOUTUBE_NICHE
    max_results = max_results or config.MAX_RESULTS

    youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)

    # First pass: search for video IDs
    search_resp = youtube.search().list(
        q=niche,
        part="snippet",
        type="video",
        order="viewCount",
        videoDuration="medium",   # 4–20 min — good for clipping
        maxResults=max_results,
        relevanceLanguage="en",
        safeSearch="none",
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
    if not video_ids:
        return []

    # Second pass: get view counts + duration
    details_resp = youtube.videos().list(
        id=",".join(video_ids),
        part="snippet,statistics,contentDetails",
    ).execute()

    videos = []
    for item in details_resp.get("items", []):
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        videos.append({
            "title": snippet["title"],
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "views": stats.get("viewCount", "0"),
            "duration": _format_duration(item["contentDetails"]["duration"]),
            "channel": snippet["channelTitle"],
            "publish_date": snippet["publishedAt"][:10],
        })

    return videos


def run(niche: str | None = None, max_results: int | None = None) -> None:
    print(f"[Collector] Searching YouTube for: {niche or config.YOUTUBE_NICHE}")
    videos = fetch_trending_videos(niche, max_results)
    print(f"[Collector] Found {len(videos)} videos")

    ws = get_sheet()
    added = append_videos(ws, videos)
    print(f"[Collector] Added {added} new rows to '{config.SPREADSHEET_NAME}' (skipped {len(videos) - added} duplicates)")
