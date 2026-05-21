"""
extractor.py
Extracts sticker codes and their bounding boxes from the Ludopédio sticker control PDF.

Each sticker code (e.g. FWC1, MEX3, CC14) is extracted as text with its exact
position on the page. That position is later used to sample the cell background
color and determine if the sticker has been collected.

EXPECTED_TOTAL: 996 stickers across 50 groups.
"""

import re
import fitz  # PyMuPDF

# '00' is a special sticker with no letter prefix; all others follow [A-Z]+[0-9]+
STICKER_PATTERN = re.compile(r"^(?:[A-Z]{1,5}\d{1,3}[a-z]?|00)$")
EXPECTED_TOTAL = 994


def extract_stickers(pdf_path: str) -> list[dict]:
    """
    Parse the PDF and return a list of dicts, one per sticker found:
        {
            "code":  "FWC1",
            "group": "FWC",
            "num":   1,
            "bbox":  (x0, y0, x1, y1),   # PDF points (72 dpi coords)
            "page":  0,
        }

    Also prints a warning if the count differs from EXPECTED_TOTAL.
    """
    doc = fitz.open(pdf_path)
    stickers = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") != 0:  # skip image blocks
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if STICKER_PATTERN.match(text):
                        if text == "00":
                            group, num = "00", 0
                        else:
                            m = re.match(r"^([A-Z]+)(\d+)([a-z]?)$", text)
                            group = m.group(1)
                            num = int(m.group(2))
                        stickers.append(
                            {
                                "code": text,
                                "group": group,
                                "num": num,
                                "bbox": tuple(span["bbox"]),  # (x0,y0,x1,y1)
                                "page": page_num,
                            }
                        )

    doc.close()

    found = len(stickers)
    if found != EXPECTED_TOTAL:
        print(
            f"[WARNING] Expected {EXPECTED_TOTAL} stickers but extracted {found}. "
            f"Difference: {EXPECTED_TOTAL - found} sticker(s) not found in PDF text layer."
        )
    else:
        print(f"[OK] All {EXPECTED_TOTAL} stickers extracted from PDF text layer.")

    return stickers


def group_summary(stickers: list[dict]) -> dict[str, list[str]]:
    """Returns a dict mapping group name → sorted list of codes in that group."""
    groups: dict[str, list] = {}
    for s in stickers:
        groups.setdefault(s["group"], []).append(s)
    return {
        g: [s["code"] for s in sorted(items, key=lambda x: x["num"])]
        for g, items in sorted(groups.items())
    }
