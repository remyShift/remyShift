"""Generate the profile banner: ASCII portrait and identity panel, one screen.

Laid out like real neofetch output, logo on the left and key/values on the
right, in a single full-width panel rather than two squares. The panel carries
its own prompt line, so the README needs no heading above it.

The portrait types itself row by row while the identity lines slide in; both
freeze once played. Nothing loops: a README sits on screen indefinitely and a
permanently animated element pulls the eye for nothing.

Usage: python scripts/make_banner.py [portrait] [destination]
"""

import sys
from pathlib import Path
from xml.sax.saxutils import escape

import ascii_art
import chassis
from palette import INK, INK_DARK, INK_DIM, INK_LIGHT, KEY, MONO, SCREEN_DARK, SCREEN_LIGHT

TITLE = chassis.USER

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

PORTRAIT_COLS = 70
CELL_W = 5.4
CELL_H = 9.3
GLYPH_SIZE = 9.0

COLUMN_GAP = 30.0
INFO_W = 357.0

TITLE_H = 32.0
LINE_H = 29.0
KEY_W = 84.0
FONT = 11.5

ROW_REVEAL = 0.30
ROW_STAGGER = 0.032
LINE_REVEAL = 0.34
LINE_STAGGER = 0.10


def build_svg(matrix, invert: bool = False) -> str:
    screen = SCREEN_DARK if invert else SCREEN_LIGHT
    glyph_ink = INK_LIGHT if invert else INK_DARK
    rows, cols = matrix.shape

    portrait_w = cols * CELL_W
    portrait_h = rows * CELL_H
    info_h = TITLE_H + len(ROWS) * LINE_H

    content_w = portrait_w + COLUMN_GAP + INFO_W
    content_h = max(portrait_h, info_h)
    width, height = chassis.canvas_size(content_w, content_h)
    ox, oy = chassis.content_origin()

    portrait_y = oy + (content_h - portrait_h) / 2
    info_x = ox + portrait_w + COLUMN_GAP
    info_y = oy + (content_h - info_h) / 2

    # The identity lines start once the portrait is roughly drawn, so the eye
    # is not asked to follow two things at once.
    info_delay = rows * ROW_STAGGER * 0.55

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
        f'aria-label="ASCII portrait and identity card for {TITLE}">',
        "<style>",
        *chassis.styles(),
        f".mono{{font-family:{MONO};white-space:pre}}",
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
        parts.append(f".s{i}{{animation-delay:{info_delay + i * LINE_STAGGER:.2f}s}}")
    parts.append("</style>")

    parts.extend(
        f.replace(f'fill="{chassis.SCREEN}"', f'fill="{screen}"')
        for f in chassis.build(width, height, chassis.prompt("whoiam"))
    )

    parts.append("<defs>")
    # One wipe mask per portrait row, staggered in time.
    for r in range(rows):
        parts.append(
            f'<clipPath id="w{r}">'
            f'<rect x="{ox:.1f}" y="{portrait_y + r * CELL_H:.1f}" '
            f'width="0" height="{CELL_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{portrait_w:.1f}" '
            f'dur="{ROW_REVEAL}s" begin="{r * ROW_STAGGER:.3f}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
    parts.append("</defs>")

    for r in range(rows):
        segments = ascii_art.runs_for_row(matrix[r])
        if not segments:
            continue
        y = portrait_y + GLYPH_SIZE + r * CELL_H
        parts.append(f'<g clip-path="url(#w{r})">')
        for col, text in segments:
            # textLength pins each segment to the grid, so alignment does not
            # depend on the metrics of whichever monospace font the reader has.
            parts.append(
                f'<text class="mono" x="{ox + col * CELL_W:.1f}" y="{y:.1f}" '
                f'font-size="{GLYPH_SIZE}" fill="{glyph_ink}" '
                f'textLength="{len(text) * CELL_W:.1f}" '
                f'lengthAdjust="spacingAndGlyphs">{escape(text)}</text>'
            )
        parts.append("</g>")

    parts.append(
        f'<text class="t ttl ln s0" x="{info_x:.1f}" y="{info_y + 12:.1f}">'
        f"{escape(TITLE)}</text>"
    )
    parts.append(
        f'<line class="rule ln s1" x1="{info_x:.1f}" y1="{info_y + 18:.1f}" '
        f'x2="{info_x + INFO_W:.1f}" y2="{info_y + 18:.1f}"/>'
    )
    for i, (key, value) in enumerate(ROWS):
        y = info_y + TITLE_H + 12 + i * LINE_H
        parts.append(
            f'<text class="t key ln s{i + 2}" x="{info_x:.1f}" y="{y:.1f}">'
            f"{escape(key)}</text>"
        )
        parts.append(
            f'<text class="t val ln s{i + 2}" x="{info_x + KEY_W:.1f}" y="{y:.1f}">'
            f"{escape(value)}</text>"
        )

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:] if a != "--invert"]
    invert = "--invert" in sys.argv
    source = Path(argv[0]) if argv else Path("data/portrait-prepped.png")
    target = Path(argv[1]) if len(argv) > 1 else Path("banner.svg")
    grid = ascii_art.trim(
        ascii_art.load_matrix(source, PORTRAIT_COLS, CELL_W, CELL_H, invert)
    )
    svg = build_svg(grid, invert)
    target.write_text(svg, encoding="utf-8")
    print(f"wrote {target}: {grid.shape[1]}x{grid.shape[0]} portrait, {len(svg) / 1024:.1f} KB")
