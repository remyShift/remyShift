"""Turn the prepared portrait into an animated ASCII SVG.

Each row of glyphs is revealed by a horizontal wipe, staggered in time, which
reads as typing. Everything is SMIL plus embedded CSS: GitHub strips
JavaScript and inline styles from READMEs, but animations contained inside an
SVG served as an image go through.

Usage: python scripts/make_ascii_svg.py [source] [destination] [--invert]
"""

import sys
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

import chassis
from palette import INK_DARK, INK_LIGHT, MONO, SCREEN_DARK, SCREEN_LIGHT

# Density ramp, lightest to densest.
RAMP = " .`:-=+*cs#%@"

COLS = 96
CELL_W = 6.6
CELL_H = 11.4
FONT_SIZE = 11.0

ROW_REVEAL = 0.34
ROW_STAGGER = 0.055

BACKGROUND_CUTOFF = 250


def load_matrix(src: Path, invert: bool = False):
    """Return the normalised luminance grid (0 = black, 1 = white)."""
    im = Image.open(src).convert("L")
    if invert:
        # The background was flattened to pure white: inverting it would make
        # it denser than the subject and drown the whole frame. Excluded, it
        # stays empty and the dark screen shows through.
        arr = np.asarray(im)
        background = arr >= BACKGROUND_CUTOFF
        flipped = 255 - arr
        flipped[background] = 255
        im = Image.fromarray(flipped)
    rows = max(1, round(COLS * (im.height / im.width) * (CELL_W / CELL_H)))
    small = im.resize((COLS, rows), Image.LANCZOS)
    return np.asarray(small).astype(np.float32) / 255.0


def runs_for_row(values: np.ndarray):
    """Split a row into ink segments separated by blanks.

    One element per segment, not one per character: without this the SVG runs
    into the hundreds of kilobytes.
    """
    glyphs = []
    for v in values:
        darkness = 1.0 - float(v)
        glyphs.append(RAMP[min(int(darkness * len(RAMP)), len(RAMP) - 1)])

    out, start = [], None
    for i, ch in enumerate(glyphs + [" "]):
        if ch == " ":
            if start is not None:
                out.append((start, "".join(glyphs[start:i])))
                start = None
        elif start is None:
            start = i
    return out


def build_svg(matrix: np.ndarray, invert: bool = False) -> str:
    screen = SCREEN_DARK if invert else SCREEN_LIGHT
    ink = INK_LIGHT if invert else INK_DARK
    rows, cols = matrix.shape
    grid_w = cols * CELL_W
    grid_h = rows * CELL_H

    width, height = chassis.canvas_size(grid_w, grid_h)
    ox, oy = chassis.content_origin()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
        f'aria-label="ASCII portrait">',
        "<style>",
        *chassis.styles(),
        f".mono{{font-family:{MONO};white-space:pre}}",
        "</style>",
        # The portrait is the one panel whose screen can differ from the theme,
        # so it overrides the chassis screen fill rather than using it as is.
        *[
            f.replace(f'fill="{chassis.SCREEN}"', f'fill="{screen}"')
            for f in chassis.build(width, height, "remy@github ~ $ ./portrait.sh")
        ],
        "<defs>",
    ]

    # One wipe mask per row, staggered in time.
    for r in range(rows):
        begin = f"{r * ROW_STAGGER:.3f}s"
        parts.append(
            f'<clipPath id="w{r}">'
            f'<rect x="{ox:.1f}" y="{oy + r * CELL_H:.1f}" '
            f'width="0" height="{CELL_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{grid_w:.1f}" '
            f'dur="{ROW_REVEAL}s" begin="{begin}" fill="freeze"/>'
            f"</rect></clipPath>"
        )
    parts.append("</defs>")

    for r in range(rows):
        segments = runs_for_row(matrix[r])
        if not segments:
            continue
        y = oy + FONT_SIZE + r * CELL_H
        parts.append(f'<g clip-path="url(#w{r})">')
        for col, text in segments:
            x = ox + col * CELL_W
            # textLength pins each segment to the grid, so alignment does not
            # depend on the metrics of whichever monospace font the reader has.
            parts.append(
                f'<text class="mono" x="{x:.1f}" y="{y:.1f}" '
                f'font-size="{FONT_SIZE}" fill="{ink}" '
                f'textLength="{len(text) * CELL_W:.1f}" '
                f'lengthAdjust="spacingAndGlyphs">{escape(text)}</text>'
            )
        parts.append("</g>")

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:] if a != "--invert"]
    invert = "--invert" in sys.argv
    source = Path(argv[0]) if argv else Path("data/portrait-prepped.png")
    target = Path(argv[1]) if len(argv) > 1 else Path("remy-ascii.svg")
    grid = load_matrix(source, invert)
    svg = build_svg(grid, invert)
    target.write_text(svg, encoding="utf-8")
    print(
        f"wrote {target}: {grid.shape[1]}x{grid.shape[0]} grid, "
        f"{len(svg) / 1024:.1f} KB"
    )
