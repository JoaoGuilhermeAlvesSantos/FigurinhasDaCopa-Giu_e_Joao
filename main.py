"""
main.py
Entry point: reads the PDF, analyses cell colours, validates the total count
against the expected 996, and outputs results as JSON and CSV.

Usage:
    python main.py [PDF_PATH] [OPTIONS]

Options:
    --dpi INT          Render resolution (default: 200)
    --threshold FLOAT  White-fraction threshold (default: 0.70)
    --expand FLOAT     Cell expansion in PDF points (default: 1.5)
    --debug-image PATH Save rendered page PNG for visual inspection
    --output-json PATH JSON output file (default: results.json)
    --output-csv  PATH CSV  output file (default: results.csv)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from extractor import EXPECTED_TOTAL, extract_stickers, group_summary
from color_analyzer import DEFAULT_DPI, WHITE_THRESHOLD, CELL_EXPAND_PT, analyze, summarize


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Conta figurinhas – Ludopédio Copa 2026")
    p.add_argument("pdf", nargs="?", default="Controle_Figurinhas_Ludopedio_pdf.pdf")
    p.add_argument("--dpi",        type=int,   default=DEFAULT_DPI)
    p.add_argument("--threshold",  type=float, default=WHITE_THRESHOLD)
    p.add_argument("--expand",     type=float, default=CELL_EXPAND_PT)
    p.add_argument("--debug-image",            default=None,           metavar="PATH")
    p.add_argument("--output-json",            default="results.json", metavar="PATH")
    p.add_argument("--output-csv",             default="results.csv",  metavar="PATH")
    return p.parse_args()


def write_json(summary: dict, results, path: str) -> None:
    data = {
        "summary": {
            "total":     summary["total"],
            "collected": summary["collected"],
            "missing":   summary["missing"],
            "expected":  EXPECTED_TOTAL,
            "count_ok":  summary["total"] == EXPECTED_TOTAL,
        },
        "by_group": summary["by_group"],
        "all_stickers": [
            {
                "code":           r.code,
                "group":          r.group,
                "collected":      r.collected,
                "white_fraction": round(r.white_fraction, 4),
                "avg_rgb":        list(r.avg_rgb),
            }
            for r in sorted(results, key=lambda r: (r.group, r.num))
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON written to {path}")


def write_csv(results, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "group", "num", "collected", "white_fraction",
                         "avg_r", "avg_g", "avg_b"])
        for r in sorted(results, key=lambda r: (r.group, r.num)):
            writer.writerow([
                r.code, r.group, r.num,
                "yes" if r.collected else "no",
                round(r.white_fraction, 4),
                r.avg_rgb[0], r.avg_rgb[1], r.avg_rgb[2],
            ])
    print(f"[OK] CSV  written to {path}")


def main() -> int:
    args = parse_args()

    if not Path(args.pdf).exists():
        print(f"[ERROR] PDF not found: {args.pdf}", file=sys.stderr)
        return 1

    # ── 1. Extract sticker codes + positions ─────────────────────────────────
    print(f"\n=== Step 1: Extracting sticker codes from {args.pdf} ===")
    stickers = extract_stickers(args.pdf)

    summary_groups = group_summary(stickers)
    print(f"       Groups found: {len(summary_groups)}")
    for grp, codes in summary_groups.items():
        print(f"         {grp:6s}: {len(codes):3d} stickers")

    # ── 2. Validate count ────────────────────────────────────────────────────
    print(f"\n=== Step 2: Count validation ===")
    extracted = len(stickers)
    if extracted == EXPECTED_TOTAL:
        print(f"[PASS] {extracted} stickers extracted == {EXPECTED_TOTAL} expected.")
    else:
        diff = EXPECTED_TOTAL - extracted
        print(
            f"[WARN] {extracted} stickers extracted, expected {EXPECTED_TOTAL}. "
            f"{abs(diff)} {'extra' if diff < 0 else 'missing'} from PDF text layer."
        )
        print("       These stickers will not appear in the output.")

    # ── 3. Analyse cell colours ───────────────────────────────────────────────
    print(f"\n=== Step 3: Analysing cell colours (DPI={args.dpi}, threshold={args.threshold}) ===")
    results = analyze(
        args.pdf,
        stickers,
        dpi=args.dpi,
        white_threshold=args.threshold,
        expand_pt=args.expand,
        save_debug_image=args.debug_image,
    )

    # ── 4. Summarise ─────────────────────────────────────────────────────────
    print(f"\n=== Step 4: Summary ===")
    smry = summarize(results)
    print(f"  Cells analysed : {smry['total']}")
    print(f"  Collected      : {smry['collected']}  ({smry['collected']/smry['total']*100:.1f}%)")
    print(f"  Missing        : {smry['missing']}   ({smry['missing']/smry['total']*100:.1f}%)")

    import re as _re
    _num = lambda c: int(_re.search(r"\d+", c).group())

    print("\n  Missing stickers by group:")
    for grp, data in sorted(smry["by_group"].items()):
        miss = data["missing"]
        if miss:
            print(f"    {grp:6s}: {', '.join(sorted(miss, key=_num))}")

    # ── 5. Write outputs ──────────────────────────────────────────────────────
    print(f"\n=== Step 5: Writing outputs ===")
    write_json(smry, results, args.output_json)
    write_csv(results, args.output_csv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
