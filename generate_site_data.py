"""
generate_site_data.py
Reads results.json and writes docs/data.js containing the full ALBUM_DATA
JavaScript constant used by the static site.

Run after main.py:
    python generate_site_data.py
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

# ── Team metadata ─────────────────────────────────────────────────────────────
# (code, name_pt, flag_emoji, tournament_group, is_host)
TEAMS: list[tuple] = [
    # Group A
    ("MEX", "México",         "🇲🇽", "A", True),
    ("RSA", "África do Sul",  "🇿🇦", "A", False),
    ("KOR", "Coreia do Sul",  "🇰🇷", "A", False),
    ("CZE", "Rep. Tcheca",    "🇨🇿", "A", False),
    # Group B
    ("CAN", "Canadá",         "🇨🇦", "B", True),
    ("BIH", "Bósnia",         "🇧🇦", "B", False),
    ("QAT", "Catar",          "🇶🇦", "B", False),
    ("SUI", "Suíça",          "🇨🇭", "B", False),
    # Group C
    ("BRA", "Brasil",         "🇧🇷", "C", False),
    ("MAR", "Marrocos",       "🇲🇦", "C", False),
    ("HAI", "Haiti",          "🇭🇹", "C", False),
    ("SCO", "Escócia",        "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "C", False),
    # Group D
    ("USA", "Estados Unidos", "🇺🇸", "D", True),
    ("PAR", "Paraguai",       "🇵🇾", "D", False),
    ("AUS", "Austrália",      "🇦🇺", "D", False),
    ("TUR", "Turquia",        "🇹🇷", "D", False),
    # Group E
    ("GER", "Alemanha",       "🇩🇪", "E", False),
    ("CUW", "Curaçao",        "🇨🇼", "E", False),
    ("CIV", "Costa do Marfim","🇨🇮", "E", False),
    ("ECU", "Equador",        "🇪🇨", "E", False),
    # Group F
    ("NED", "Holanda",        "🇳🇱", "F", False),
    ("JPN", "Japão",          "🇯🇵", "F", False),
    ("SWE", "Suécia",         "🇸🇪", "F", False),
    ("TUN", "Tunísia",        "🇹🇳", "F", False),
    # Group G
    ("BEL", "Bélgica",        "🇧🇪", "G", False),
    ("EGY", "Egito",          "🇪🇬", "G", False),
    ("IRN", "Irã",            "🇮🇷", "G", False),
    ("NZL", "Nova Zelândia",  "🇳🇿", "G", False),
    # Group H
    ("ESP", "Espanha",        "🇪🇸", "H", False),
    ("CPV", "Cabo Verde",     "🇨🇻", "H", False),
    ("KSA", "Arábia Saudita", "🇸🇦", "H", False),
    ("URU", "Uruguai",        "🇺🇾", "H", False),
    # Group I
    ("FRA", "França",         "🇫🇷", "I", False),
    ("SEN", "Senegal",        "🇸🇳", "I", False),
    ("IRQ", "Iraque",         "🇮🇶", "I", False),
    ("NOR", "Noruega",        "🇳🇴", "I", False),
    # Group J
    ("ARG", "Argentina",      "🇦🇷", "J", False),
    ("ALG", "Argélia",        "🇩🇿", "J", False),
    ("AUT", "Áustria",        "🇦🇹", "J", False),
    ("JOR", "Jordânia",       "🇯🇴", "J", False),
    # Group K
    ("POR", "Portugal",       "🇵🇹", "K", False),
    ("COD", "Congo",          "🇨🇩", "K", False),
    ("UZB", "Uzbequistão",    "🇺🇿", "K", False),
    ("COL", "Colômbia",       "🇨🇴", "K", False),
    # Group L
    ("ENG", "Inglaterra",     "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "L", False),
    ("CRO", "Croácia",        "🇭🇷", "L", False),
    ("GHA", "Gana",           "🇬🇭", "L", False),
    ("PAN", "Panamá",         "🇵🇦", "L", False),
    # Special sections
    ("FWC", "FIFA World Cup History", "🏆", "–", False),
    ("CC",  "Coca-Cola",              "🥤", "–", False),
    ("00",  "Especial",               "⭐", "–", False),
]

TEAM_META: dict[str, dict] = {
    code: {"name": name, "flag": flag, "group": group, "isHost": is_host}
    for code, name, flag, group, is_host in TEAMS
}


def load_results(path: str = "results.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_team_stats(results: dict) -> list[dict]:
    """
    Returns a list of team stat dicts, one per group code (MEX, FWC, etc.).
    """
    by_group = results["by_group"]
    teams = []

    for code, meta in TEAM_META.items():
        grp_data = by_group.get(code, {"collected": [], "missing": []})
        collected_codes = grp_data["collected"]
        missing_codes   = grp_data["missing"]
        total = len(collected_codes) + len(missing_codes)
        n_collected = len(collected_codes)
        pct = round(n_collected / total * 100, 1) if total > 0 else 0.0

        # Sort missing codes numerically
        import re
        def sort_key(c):
            m = re.search(r"\d+", c)
            return int(m.group()) if m else 0

        teams.append({
            "code":      code,
            "name":      meta["name"],
            "flag":      meta["flag"],
            "group":     meta["group"],
            "isHost":    meta["isHost"],
            "total":     total,
            "collected": n_collected,
            "percent":   pct,
            "missing":   sorted(missing_codes, key=sort_key),
        })

    # Preserve the order defined in TEAMS so the site follows the expected sequence.
    return teams


def build_group_stats(teams: list[dict]) -> list[dict]:
    """Aggregate stats per tournament group (A–L)."""
    groups: dict[str, dict] = {}
    for t in teams:
        g = t["group"]
        if g == "–":
            continue
        if g not in groups:
            groups[g] = {"letter": g, "total": 0, "collected": 0, "teams": []}
        groups[g]["total"]     += t["total"]
        groups[g]["collected"] += t["collected"]
        groups[g]["teams"].append(t["code"])

    result = []
    for g in "ABCDEFGHIJKL":
        if g in groups:
            d = groups[g]
            d["percent"] = round(d["collected"] / d["total"] * 100, 1) if d["total"] else 0
            result.append(d)
    return result


def generate(results_path: str = "results.json", out_path: str = "docs/data.js") -> None:
    print(f"Reading {results_path}...")
    raw = load_results(results_path)

    summary = raw["summary"]
    total     = summary["total"]
    collected = summary["collected"]
    missing   = summary["missing"]
    percent   = round(collected / total * 100, 1) if total else 0

    teams  = build_team_stats(raw)
    groups = build_group_stats(teams)

    # Separate regular teams vs special sections
    regular_teams   = [t for t in teams if t["group"] != "–"]
    special_sections = [t for t in teams if t["group"] == "–"]

    complete_teams = sum(1 for t in regular_teams if t["percent"] == 100)

    data = {
        "meta": {
            "title":   "🧡 Figurinhas da Prof Giu",
            "album":   "Copa do Mundo 2026",
            "total":     total,
            "collected": collected,
            "missing":   missing,
            "percent":   percent,
            "completeTeams": complete_teams,
            "updated": date.today().isoformat(),
            "packsBought": 90,
        },
        "teams":    teams,
        "groups":   groups,
        "special":  special_sections,
    }

    # Validate
    assert total == 994, f"Expected 994, got {total}"
    assert collected + missing == total, "collected + missing ≠ total"
    print(f"[PASS] total={total}  collected={collected}  missing={missing}  pct={percent}%")

    # Write JS file
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    js_content = f"// Auto-generated by generate_site_data.py – {date.today()}\n"
    js_content += "const ALBUM_DATA = "
    js_content += json.dumps(data, ensure_ascii=False, indent=2)
    js_content += ";\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"[OK] Written to {out_path}  ({len(js_content):,} bytes)")
    print(f"     {len(regular_teams)} teams + {len(special_sections)} special sections")


if __name__ == "__main__":
    generate()
