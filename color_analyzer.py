"""
color_analyzer.py
Renders the PDF page to a bitmap and samples the background color of each
sticker cell to decide if the sticker has been collected.

HOW IT WORKS
------------
1. The PDF is rendered at a chosen DPI (default 200) so cells are large enough
   to sample reliably.
2. For each sticker we know the text bounding box (PDF points). We expand it by
   a fixed margin to approximate the full cell area.
3. Inside that cell area we:
     a. Exclude very dark pixels (the text characters themselves, ~black).
     b. Measure the fraction of remaining pixels that are "near-white"
        (R > 230, G > 230, B > 230).
4. A cell is considered COLLECTED if the white fraction is below WHITE_THRESHOLD
   (default 0.70), meaning the person has filled it with colour.
   A cell is considered MISSING if the white fraction is ≥ WHITE_THRESHOLD.

The threshold and DPI are configurable so the caller can tune them after
visually inspecting the output image.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

# ── tuneable constants ────────────────────────────────────────────────────────
DEFAULT_DPI: int = 200          # render resolution (higher = more accurate)
CELL_EXPAND_PT: float = 1.5     # points to expand the text bbox on each side
                                 # to cover the cell background
WHITE_THRESHOLD: float = 0.70   # cells with ≥ this fraction of white pixels
                                 # are considered MISSING (sticker not collected)
DARK_THRESHOLD: int = 60        # pixels with max(R,G,B) ≤ this value are
                                 # treated as text/ink and ignored
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class CellResult:
    code: str
    group: str
    num: int
    page: int
    bbox_pdf: tuple          # (x0, y0, x1, y1) in PDF points
    white_fraction: float
    avg_rgb: tuple           # (R, G, B) of non-dark pixels, 0-255
    collected: bool          # True  → sticker collected (cell is coloured)
                             # False → sticker missing   (cell is white)
    note: str = ""           # e.g. "bbox too small" for debugging


def _render_page(pdf_path: str, page_num: int, dpi: int) -> tuple[Image.Image, float]:
    """
    Returns (PIL Image in RGB mode, scale factor used).
    scale = dpi / 72  because PDF points are at 72 dpi.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    doc.close()
    return img, scale


def _sample_cell(
    img_array: np.ndarray,
    bbox_pdf: tuple,
    scale: float,
    expand_pt: float,
) -> tuple[float, tuple]:
    """
    Crop the cell region from img_array and return (white_fraction, avg_rgb).
    avg_rgb excludes very dark pixels (text).
    """
    x0, y0, x1, y1 = bbox_pdf
    # Expand to include full cell background
    x0 = max(0, (x0 - expand_pt) * scale)
    y0 = max(0, (y0 - expand_pt) * scale)
    x1 = min(img_array.shape[1], (x1 + expand_pt) * scale)
    y1 = min(img_array.shape[0], (y1 + expand_pt) * scale)

    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)

    if x1 <= x0 or y1 <= y0:
        return 1.0, (255, 255, 255)  # degenerate bbox → treat as white/missing

    cell = img_array[y0:y1, x0:x1]  # shape: (H, W, 3)

    # Mask out dark pixels (text/ink)
    max_channel = cell.max(axis=2)          # (H, W)
    non_dark = max_channel > DARK_THRESHOLD  # boolean mask
    visible = cell[non_dark]               # shape: (N, 3)

    if visible.size == 0:
        return 1.0, (255, 255, 255)

    avg_rgb = tuple(visible.mean(axis=0).astype(int).tolist())

    # Near-white: all channels > 230
    white_mask = np.all(visible > 230, axis=1)
    white_fraction = float(white_mask.sum() / len(visible))

    return white_fraction, avg_rgb


def analyze(
    pdf_path: str,
    stickers: list[dict],
    dpi: int = DEFAULT_DPI,
    white_threshold: float = WHITE_THRESHOLD,
    expand_pt: float = CELL_EXPAND_PT,
    save_debug_image: Optional[str] = None,
) -> list[CellResult]:
    """
    Main entry point.  Receives the list produced by extractor.extract_stickers()
    and returns a CellResult for each sticker.

    Parameters
    ----------
    pdf_path        : path to the PDF file
    stickers        : list of dicts from extractor.extract_stickers()
    dpi             : render resolution
    white_threshold : fraction of white pixels above which cell = MISSING
    expand_pt       : how many PDF points to expand the text bbox per side
    save_debug_image: if a path string is given, saves the rendered page PNG there
    """
    # Group stickers by page so we only render each page once
    pages: dict[int, list[dict]] = {}
    for s in stickers:
        pages.setdefault(s["page"], []).append(s)

    results: list[CellResult] = []

    for page_num, page_stickers in sorted(pages.items()):
        img, scale = _render_page(pdf_path, page_num, dpi)
        arr = np.array(img)

        if save_debug_image:
            img.save(save_debug_image)
            print(f"[DEBUG] Saved rendered page to {save_debug_image}")

        for s in page_stickers:
            wf, avg = _sample_cell(arr, s["bbox"], scale, expand_pt)
            collected = wf < white_threshold

            results.append(
                CellResult(
                    code=s["code"],
                    group=s["group"],
                    num=s["num"],
                    page=page_num,
                    bbox_pdf=s["bbox"],
                    white_fraction=wf,
                    avg_rgb=avg,
                    collected=collected,
                )
            )

    return results


def summarize(results: list[CellResult]) -> dict:
    """
    Returns a summary dict:
        {
            "total":     int,
            "collected": int,
            "missing":   int,
            "by_group":  { "FWC": {"collected": [...], "missing": [...]}, ... }
        }
    """
    collected = [r for r in results if r.collected]
    missing   = [r for r in results if not r.collected]

    by_group: dict[str, dict] = {}
    for r in results:
        g = by_group.setdefault(r.group, {"collected": [], "missing": []})
        if r.collected:
            g["collected"].append(r.code)
        else:
            g["missing"].append(r.code)

    return {
        "total":     len(results),
        "collected": len(collected),
        "missing":   len(missing),
        "by_group":  by_group,
    }
