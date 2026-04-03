"""Google Sheets client for the Video Vault spreadsheet."""
from __future__ import annotations

import gspread
from google.oauth2.service_account import Credentials

import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

HEADERS = [
    "Title", "URL", "Views", "Duration", "Channel",
    "Publish Date", "Status", "Timestamp",
]


def _connect() -> gspread.Spreadsheet:
    creds = Credentials.from_service_account_file(
        str(config.GOOGLE_SERVICE_ACCOUNT_PATH), scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    return gc.open(config.SPREADSHEET_NAME)


def get_sheet() -> gspread.Worksheet:
    """Return (or create) the first sheet with correct headers."""
    book = _connect()
    try:
        ws = book.sheet1
    except gspread.exceptions.WorksheetNotFound:
        ws = book.add_worksheet(title="Sheet1", rows=1000, cols=len(HEADERS))

    if ws.row_values(1) != HEADERS:
        ws.insert_row(HEADERS, index=1)
    return ws


def existing_urls(ws: gspread.Worksheet) -> set[str]:
    url_col = HEADERS.index("URL") + 1
    return set(ws.col_values(url_col)[1:])  # skip header


def append_videos(ws: gspread.Worksheet, videos: list[dict]) -> int:
    """Append videos not already in the sheet. Returns number of rows added."""
    seen = existing_urls(ws)
    rows = []
    for v in videos:
        if v["url"] in seen:
            continue
        rows.append([
            v["title"], v["url"], v["views"], v["duration"],
            v["channel"], v["publish_date"], "Pending", "",
        ])
        seen.add(v["url"])
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
    return len(rows)


def next_pending(ws: gspread.Worksheet) -> tuple[int, dict] | tuple[None, None]:
    """Return (row_index, video_dict) for the first Pending row, or (None, None)."""
    status_col = HEADERS.index("Status") + 1
    statuses = ws.col_values(status_col)[1:]  # skip header
    for i, status in enumerate(statuses):
        if status == "Pending":
            row_num = i + 2  # 1-based + header
            row = ws.row_values(row_num)
            return row_num, {
                "title": row[0],
                "url": row[1],
                "views": row[2],
                "duration": row[3],
                "channel": row[4],
                "publish_date": row[5],
            }
    return None, None


def mark_done(ws: gspread.Worksheet, row_num: int, timestamp: str) -> None:
    status_col = HEADERS.index("Status") + 1
    ts_col = HEADERS.index("Timestamp") + 1
    ws.update_cell(row_num, status_col, "Done")
    ws.update_cell(row_num, ts_col, timestamp)
