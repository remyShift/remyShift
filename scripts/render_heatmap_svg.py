"""Render the contribution calendar as an animated SVG.

Cells fade in as a diagonal wave: the delay depends on (week + weekday), which
sweeps the grid from the top-left corner to the bottom-right. One delay class
per diagonal rather than an inline style per cell, otherwise the SVG doubles
in size.

Usage: python scripts/render_heatmap_svg.py [source] [destination]
"""

import json
import sys
from datetime import date
from pathlib import Path

import chassis
from palette import INK, INK_DIM, LEVELS

CELL = 11.0
GAP = 3.0
PITCH = CELL + GAP
RADIUS = 2.5

LABEL_W = 26.0
MONTH_H = 16.0
LEGEND_H = 22.0
LEGEND_LABEL_W = 30.0

WAVE_STEP = 0.018
CELL_REVEAL = 0.42

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = {1: "Mon", 3: "Wed", 5: "Fri"}


def month_labels(weeks: list) -> list:
    """Position of month names: at the first week of each month."""
    out, seen = [], set()
    for index, week in enumerate(weeks):
        if not week:
            continue
        first = date.fromisoformat(week[0]["date"])
        key = (first.year, first.month)
        if key in seen or first.day > 7:
            continue
        seen.add(key)
        out.append((index, MONTHS[first.month - 1]))
    return out


def build_svg(payload: dict) -> str:
    weeks = payload["weeks"]
    grid_w = len(weeks) * PITCH - GAP
    grid_h = 7 * PITCH - GAP

    content_w = LABEL_W + grid_w
    content_h = MONTH_H + grid_h + LEGEND_H
    width, height = chassis.canvas_size(content_w, content_h)
    ox, oy = chassis.content_origin()

    grid_x = ox + LABEL_W
    grid_y = oy + MONTH_H

    longest = max((len(w) for w in weeks), default=7)
    diagonals = len(weeks) + longest

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
        f'aria-label="Contribution calendar for {payload["username"]}">',
        "<style>",
        *chassis.styles(),
        f".lbl{{font-size:9px;fill:{INK_DIM}}}",
        f".tot{{font-size:10px;fill:{INK}}}",
        "@keyframes pop{from{opacity:0;transform:translate(-5px,-5px)}"
        "to{opacity:1;transform:translate(0,0)}}",
        f".c{{opacity:0;animation:pop {CELL_REVEAL}s ease-out forwards}}",
        "@media(prefers-reduced-motion:reduce){.c{animation:none;opacity:1}}",
    ]
    for d in range(diagonals):
        parts.append(f".w{d}{{animation-delay:{d * WAVE_STEP:.3f}s}}")
    parts.append("</style>")

    parts.extend(chassis.build(width, height, chassis.prompt("./contributions.sh")))

    for index, name in month_labels(weeks):
        x = grid_x + index * PITCH
        parts.append(f'<text class="t lbl" x="{x:.1f}" y="{grid_y - 5:.1f}">{name}</text>')

    for weekday, name in WEEKDAYS.items():
        y = grid_y + weekday * PITCH + CELL - 2
        parts.append(f'<text class="t lbl" x="{ox:.1f}" y="{y:.1f}">{name}</text>')

    for w, week in enumerate(weeks):
        for day in week:
            weekday = day["weekday"]
            x = grid_x + w * PITCH
            y = grid_y + weekday * PITCH
            fill = LEVELS[min(day["level"], len(LEVELS) - 1)]
            plural = "" if day["count"] == 1 else "s"
            parts.append(
                f'<rect class="c w{w + weekday}" x="{x:.1f}" y="{y:.1f}" '
                f'width="{CELL}" height="{CELL}" rx="{RADIUS}" fill="{fill}">'
                f'<title>{day["count"]} contribution{plural} on {day["date"]}</title></rect>'
            )

    legend_y = grid_y + grid_h + 15
    parts.append(
        f'<text class="t tot" x="{grid_x:.1f}" y="{legend_y:.1f}">'
        f'{payload["total"]:,} contributions in the last year</text>'
    )
    # Anchored on the right edge of the content box so "less [cells] more"
    # never spills onto the bezel.
    more_x = ox + content_w - 22
    boxes_x = more_x - len(LEVELS) * PITCH
    parts.append(
        f'<text class="t lbl" x="{boxes_x - LEGEND_LABEL_W:.1f}" '
        f'y="{legend_y:.1f}">less</text>'
    )
    for i, colour in enumerate(LEVELS):
        parts.append(
            f'<rect x="{boxes_x + i * PITCH:.1f}" y="{legend_y - 9:.1f}" '
            f'width="{CELL}" height="{CELL}" rx="{RADIUS}" fill="{colour}"/>'
        )
    parts.append(f'<text class="t lbl" x="{more_x + 2:.1f}" y="{legend_y:.1f}">more</text>')

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/contributions.json")
    target = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("contrib-heatmap.svg")
    data = json.loads(source.read_text(encoding="utf-8"))
    svg = build_svg(data)
    target.write_text(svg, encoding="utf-8")
    print(f"wrote {target}: {len(data['weeks'])} weeks, {len(svg) / 1024:.1f} KB")
