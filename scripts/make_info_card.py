"""Generate the neofetch-style identity panel as an animated SVG.

Lines appear one after another, staggered, then the panel settles. Nothing
loops: a README sits on screen indefinitely and a permanently blinking element
pulls the eye for nothing. Content lives here rather than in a hand-written
SVG: this is the only part of the profile edited by hand, it may as well be
readable.

Usage: python scripts/make_info_card.py [destination]
"""

import sys
from pathlib import Path
from xml.sax.saxutils import escape

import chassis
from palette import INK, INK_DIM, KEY

TITLE = "remy@github"

ROWS = [
    ("Role", "Freelance fullstack developer"),
    ("Mission", "Oli's Lab, clean cosmetics e-commerce"),
    ("Stack", "React, Next.js, Node, Payload"),
    ("Also", "TypeScript, MongoDB, Tailwind"),
    ("Learning", "ThreeJS, creative dev"),
    ("Site", "remy-shift.dev"),
    ("Contact", "contact@remy-shift.dev"),
    ("Languages", "FR, EN, KO (beginner)"),
    # Relocation line deliberately left out: it would publish a plan to move
    # abroad on a profile that clients read.
]

CONTENT_W = 366.0
TITLE_H = 34.0
# Line height tuned so the card lines up with the portrait once both are
# scaled inside the README table.
LINE_H = 30.0
KEY_W = 82.0
FONT = 11.5

LINE_REVEAL = 0.34
LINE_STAGGER = 0.11


def build_svg() -> str:
    content_h = TITLE_H + len(ROWS) * LINE_H
    width, height = chassis.canvas_size(CONTENT_W, content_h)
    ox, oy = chassis.content_origin()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
        f'aria-label="Identity card for {TITLE}">',
        "<style>",
        *chassis.styles(),
        f".ttl{{font-size:13px;fill:{KEY};font-weight:700}}",
        f".key{{font-size:{FONT}px;fill:{KEY}}}",
        f".val{{font-size:{FONT}px;fill:{INK}}}",
        f".rule{{stroke:{INK_DIM};stroke-width:1;opacity:.4}}",
        "@keyframes slide{from{opacity:0;transform:translateX(-8px)}"
        "to{opacity:1;transform:translateX(0)}}",
        f".ln{{opacity:0;animation:slide {LINE_REVEAL}s ease-out forwards}}",
        "@media(prefers-reduced-motion:reduce){.ln{animation:none;opacity:1}}",
    ]
    for i in range(len(ROWS) + 2):
        parts.append(f".s{i}{{animation-delay:{i * LINE_STAGGER:.2f}s}}")
    parts.append("</style>")

    parts.extend(chassis.build(width, height, "remy@github ~ $ neofetch"))

    parts.append(
        f'<text class="t ttl ln s0" x="{ox:.1f}" y="{oy + 12:.1f}">{escape(TITLE)}</text>'
    )
    rule_y = oy + 18
    parts.append(
        f'<line class="rule ln s1" x1="{ox:.1f}" y1="{rule_y:.1f}" '
        f'x2="{ox + CONTENT_W:.1f}" y2="{rule_y:.1f}"/>'
    )

    for i, (key, value) in enumerate(ROWS):
        y = oy + TITLE_H + 12 + i * LINE_H
        step = i + 2
        parts.append(
            f'<text class="t key ln s{step}" x="{ox:.1f}" y="{y:.1f}">{escape(key)}</text>'
        )
        parts.append(
            f'<text class="t val ln s{step}" x="{ox + KEY_W:.1f}" y="{y:.1f}">'
            f"{escape(value)}</text>"
        )


    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("info-card.svg")
    svg = build_svg()
    target.write_text(svg, encoding="utf-8")
    print(f"wrote {target}: {len(ROWS)} rows, {len(svg) / 1024:.1f} KB")
