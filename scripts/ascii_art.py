"""Turn a prepared portrait into a grid of ASCII glyphs.

Pure computation, no SVG: the banner owns the layout. Split out so the glyph
work is not tangled with chassis geometry.
"""

from pathlib import Path

import numpy as np
from PIL import Image

# Density ramp, lightest to densest.
RAMP = " .`:-=+*cs#%@"

BACKGROUND_CUTOFF = 250


def load_matrix(src: Path, cols: int, cell_w: float, cell_h: float, invert: bool = False):
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
    rows = max(1, round(cols * (im.height / im.width) * (cell_w / cell_h)))
    small = im.resize((cols, rows), Image.LANCZOS)
    return np.asarray(small).astype(np.float32) / 255.0


def trim(matrix: np.ndarray, blank: float = 0.985) -> np.ndarray:
    """Drop the fully blank rows and columns around the glyph grid.

    The prepared photo keeps uneven white margins, more on the shadow side.
    Left in, they push the portrait off-centre inside its column and leave
    dead space that the layout cannot account for.
    """
    ink = matrix < blank
    if not ink.any():
        return matrix
    rows = np.nonzero(ink.any(axis=1))[0]
    cols = np.nonzero(ink.any(axis=0))[0]
    return matrix[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]


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
