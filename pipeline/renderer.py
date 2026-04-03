"""Step 3 — Cinematic Visual Treatment via FFmpeg.

Applies a pure-black background with a centered, rounded-corner video inset
and subtle padding to every clip produced by the Mosaic step.

Output spec: 1080×1920 (9:16), libx264 + aac, clean minimal look.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

# ─── Layout constants (pixels, 1080×1920 canvas) ──────────────────────────
CANVAS_W = 1080
CANVAS_H = 1920
PADDING = 70          # black border on left/right
CORNER_RADIUS = 40    # rounded corner radius (pixels)

INNER_W = CANVAS_W - 2 * PADDING                    # 940
INNER_H = int(INNER_W * CANVAS_H / CANVAS_W)        # 1671 (maintains proportion)
PAD_X = PADDING                                       # 70
PAD_Y = (CANVAS_H - INNER_H) // 2                    # vertical centering


def _build_filter(w: int, h: int, r: int, pad_x: int, pad_y: int) -> str:
    """Build an FFmpeg filtergraph that scales, pads, and rounds corners.

    Strategy:
      1. Scale the input to (w × h).
      2. Pad to the full canvas with a black background.
      3. Apply a rounded-corner alpha mask using `geq`, then composite
         over a solid black canvas with `overlay`.

    The geq expression returns 255 (opaque) inside the rounded rect and
    0 (transparent) outside, allowing the black background to show through.
    """
    cw, ch = CANVAS_W, CANVAS_H

    # geq alpha expression — 1 if inside rounded rect, 0 otherwise
    # Uses the standard corner-distance formula.
    geq_alpha = (
        f"if("
        f"  lte(X,{pad_x})+lte(Y,{pad_y})+gte(X,{pad_x+w})+gte(Y,{pad_y+h}),"
        f"  0,"                          # outside bounding box → transparent
        f"  if("
        f"    gt(abs(X-{pad_x}-{w}//2), {w}//2-{r})*gt(abs(Y-{pad_y}-{h}//2), {h}//2-{r}),"
        f"    if(lte(hypot(abs(X-{pad_x}-{w}//2)-({w}//2-{r}), abs(Y-{pad_y}-{h}//2)-({h}//2-{r})),{r}), 255, 0),"
        f"    255"
        f"  )"
        f")"
    )

    return (
        f"[0:v]scale={w}:{h}[scaled];"
        f"color=black:s={cw}x{ch}[bg];"
        f"[bg][scaled]overlay={pad_x}:{pad_y}[composited];"
        f"[composited]format=yuva420p,"
        f"geq=lum='p(X,Y)':a='{geq_alpha}'[masked];"
        f"color=black:s={cw}x{ch}[black];"
        f"[black][masked]overlay=0:0,format=yuv420p[out]"
    )


def apply_cinematic_frame(input_path: Path, output_path: Path) -> Path:
    """Run FFmpeg to apply the cinematic black-border treatment.

    Args:
        input_path: Raw 9:16 clip from Mosaic.
        output_path: Destination path for the finished clip.

    Returns:
        output_path on success.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    filter_graph = _build_filter(
        w=INNER_W, h=INNER_H, r=CORNER_RADIUS,
        pad_x=PAD_X, pad_y=PAD_Y,
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-filter_complex", filter_graph,
        "-map", "[out]",
        "-map", "0:a?",           # pass through audio if present
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",             # high quality
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed for {input_path.name}:\n{result.stderr[-2000:]}")

    return output_path


def render_clips(raw_clips: list[Path], output_dir: Path) -> list[Path]:
    """Apply cinematic treatment to every raw clip.

    Returns list of finished clip paths.
    """
    finished = []
    for raw in raw_clips:
        out = output_dir / raw.name.replace("_raw", "")
        print(f"  [Renderer] {raw.name} → {out.name}")
        apply_cinematic_frame(raw, out)
        finished.append(out)
    print(f"  [Renderer] Done. {len(finished)} clips rendered.")
    return finished
