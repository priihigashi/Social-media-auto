"""Step 2 — Daily Clip Session via Mosaic API.

Uploads a YouTube video (downloaded via yt-dlp) to Mosaic, runs the
viral-moments agent, and downloads the resulting 9:16 captioned clips.
"""
from __future__ import annotations

import time
import tempfile
import subprocess
from pathlib import Path

import requests

import config

MOSAIC_BASE = config.MOSAIC_API_BASE.rstrip("/")
AUTH_HEADERS = {"Authorization": f"Bearer {config.MOSAIC_API_KEY}"}

# How long to wait (seconds) between status polls
POLL_INTERVAL = 10
# Maximum total wait time before giving up (seconds)
MAX_WAIT = 600


# ─── Download ────────────────────────────────────────────────────────────────

def download_video(url: str, dest_dir: Path) -> Path:
    """Download a YouTube video to dest_dir using yt-dlp and return the file path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(dest_dir / "%(id)s.%(ext)s")
    result = subprocess.run(
        [
            "yt-dlp",
            "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--output", output_template,
            "--no-playlist",
            url,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{result.stderr}")

    # Find the downloaded file
    files = list(dest_dir.glob("*.mp4"))
    if not files:
        raise FileNotFoundError(f"No .mp4 found in {dest_dir} after yt-dlp")
    return max(files, key=lambda p: p.stat().st_mtime)


# ─── Mosaic upload ────────────────────────────────────────────────────────────

def _get_upload_url(filename: str, content_type: str = "video/mp4") -> tuple[str, str]:
    """Request a pre-signed upload URL. Returns (upload_url, file_id)."""
    resp = requests.post(
        f"{MOSAIC_BASE}/video/get-upload-url",
        headers=AUTH_HEADERS,
        json={"filename": filename, "content_type": content_type},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["upload_url"], data["file_id"]


def _upload_file(upload_url: str, file_path: Path) -> None:
    """PUT the video bytes to the pre-signed S3 URL."""
    with open(file_path, "rb") as fh:
        put_resp = requests.put(
            upload_url,
            data=fh,
            headers={"Content-Type": "video/mp4"},
            timeout=300,
        )
    put_resp.raise_for_status()


def _finalize_upload(file_id: str) -> None:
    resp = requests.post(
        f"{MOSAIC_BASE}/video/finalize-upload",
        headers=AUTH_HEADERS,
        json={"file_id": file_id},
        timeout=30,
    )
    resp.raise_for_status()


def upload_to_mosaic(file_path: Path) -> str:
    """Upload a local video file to Mosaic and return its file_id."""
    print(f"  [Mosaic] Uploading {file_path.name} …")
    upload_url, file_id = _get_upload_url(file_path.name)
    _upload_file(upload_url, file_path)
    _finalize_upload(file_id)
    print(f"  [Mosaic] Upload complete. file_id={file_id}")
    return file_id


# ─── Agent run ───────────────────────────────────────────────────────────────

def _run_agent(file_id: str) -> str:
    """Trigger the viral-moments + captions agent. Returns run_id."""
    resp = requests.post(
        f"{MOSAIC_BASE}/run-agent",
        headers=AUTH_HEADERS,
        json={
            "file_id": file_id,
            # Mosaic agent parameters — adjust agent_id to the exact
            # viral-moments agent name shown in your Mosaic dashboard.
            "agent_id": "viral-moments",
            "params": {
                "aspect_ratio": "9:16",
                "num_clips": 5,
                "caption_color": config.CAPTION_COLOR,
                "caption_style": "clean",
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["run_id"]


def _poll_until_done(run_id: str) -> dict:
    """Poll /get-agent-run-simple/{id} until status is 'completed' or 'failed'."""
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        resp = requests.get(
            f"{MOSAIC_BASE}/get-agent-run-simple/{run_id}",
            headers=AUTH_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "")
        print(f"  [Mosaic] Agent status: {status}")
        if status == "completed":
            return data
        if status == "failed":
            raise RuntimeError(f"Mosaic agent run failed: {data}")
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"Mosaic agent run {run_id} timed out after {MAX_WAIT}s")


def _download_outputs(run_id: str, dest_dir: Path) -> list[Path]:
    """Fetch signed output URLs and download each clip."""
    resp = requests.get(
        f"{MOSAIC_BASE}/get-agent-run-outputs/{run_id}",
        headers=AUTH_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    outputs = resp.json().get("outputs", [])

    downloaded = []
    for i, item in enumerate(outputs):
        url = item.get("url") or item.get("signed_url")
        if not url:
            continue
        clip_path = dest_dir / f"clip_{i + 1:02d}_raw.mp4"
        print(f"  [Mosaic] Downloading clip {i + 1}/{len(outputs)} → {clip_path.name}")
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(clip_path, "wb") as fh:
                for chunk in r.iter_content(chunk_size=8192):
                    fh.write(chunk)
        downloaded.append(clip_path)
    return downloaded


# ─── Public entry point ───────────────────────────────────────────────────────

def extract_clips(youtube_url: str, dest_dir: Path) -> list[Path]:
    """Full pipeline: download → upload → run agent → download clips.

    Returns list of raw clip paths (before FFmpeg treatment).
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        print(f"  [Clipper] Downloading source video …")
        source = download_video(youtube_url, tmp_path)

        file_id = upload_to_mosaic(source)

    print(f"  [Clipper] Running Mosaic viral-moments agent …")
    run_id = _run_agent(file_id)
    _poll_until_done(run_id)

    dest_dir.mkdir(parents=True, exist_ok=True)
    clips = _download_outputs(run_id, dest_dir)
    print(f"  [Clipper] {len(clips)} raw clips saved to {dest_dir}")
    return clips
