"""Prepare the source photo for ASCII conversion.

Pipeline: detect the coloured ring, crop to the inner disc, flatten the
uniform background, retexture the dark mass, then frame on the head. That last
step is what makes the result readable: frame on the bust and the shoulders
are three times wider than the head, which squeezes the face into a third of
the ASCII grid columns.

Usage: python scripts/prep_photo.py <source> [destination]
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

BG_TOLERANCE = 26
RING_MARGIN = 4
INK_THRESHOLD = 245

# Ink ratio per row above which the shoulders are considered to start: the
# head plateaus around 0.40, the shoulders climb to 1.00.
SHOULDER_RATIO = 0.48
# Frame width as a multiple of head width, and how much shoulder is kept below
# the chin, as a fraction of head height.
HEAD_WIDTH_FACTOR = 1.55
SHOULDER_KEEP = 0.16
CROP_MARGIN = 8


def detect_ring(rgb: np.ndarray):
    """Return (cx, cy, inner_radius) of the coloured ring, or None."""
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    ring = (b > r + 50) & (b > g + 30)
    if ring.sum() < rgb.shape[0] * rgb.shape[1] * 0.01:
        return None
    ys, xs = np.nonzero(ring)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    outer = max(xs.max() - xs.min(), ys.max() - ys.min()) / 2
    row = ring[int(round(cy))]
    thickness = row.sum() / 2 if row.any() else outer * 0.06
    return cx, cy, outer - thickness - RING_MARGIN


def estimate_background(gray: np.ndarray) -> int:
    """Level of the uniform background, ignoring areas already whitened.

    The corners are unusable: the circular mask set them to 255. So take the
    mode of the light tones strictly below 250 instead.
    """
    light = gray[(gray > 170) & (gray < 250)]
    if light.size == 0:
        return 255
    return int(np.bincount(light.ravel()).argmax())


def flatten_background(gray: np.ndarray, bg_level: int) -> np.ndarray:
    """Crush the uniform background to pure white."""
    out = gray.copy()
    out[np.abs(gray.astype(int) - bg_level) <= BG_TOLERANCE] = 255
    return out


def retexture_shadows(gray: np.ndarray) -> np.ndarray:
    """Stretch the dark range so detail survives inside the blacks.

    Cap and t-shirt are black and cover a large share of the image: without
    this curve they both flatten onto the densest glyph and the portrait loses
    its depth.
    """
    out = gray.astype(np.float32)
    shadow = out < 96
    out[shadow] = 96.0 * np.power(out[shadow] / 96.0, 0.42)
    return np.clip(out, 0, 255).astype(np.uint8)


def crop_to_head(gray: np.ndarray) -> np.ndarray:
    """Frame on the head, keeping just enough shoulder to ground the portrait.

    The head-to-shoulder break is detected on the per-row ink profile, which
    avoids hardcoding coordinates that only fit one photo.
    """
    ink = gray < INK_THRESHOLD
    if not ink.any():
        return gray

    per_row = ink.sum(axis=1)
    widest = per_row.max()
    rows = np.nonzero(per_row > 0)[0]
    top = int(rows[0])

    flare = np.nonzero(per_row > widest * SHOULDER_RATIO)[0]
    head_end = int(flare[0]) if flare.size else int(rows[-1])
    if head_end - top < 20:  # unusual profile, keep everything
        head_end = int(rows[-1])

    head = ink[top:head_end]
    cols = np.nonzero(head.any(axis=0))[0]
    left, right = int(cols[0]), int(cols[-1])
    head_w = right - left
    head_h = head_end - top

    centre = (left + right) / 2
    half = head_w * HEAD_WIDTH_FACTOR / 2
    x0 = int(max(centre - half, 0))
    x1 = int(min(centre + half, gray.shape[1]))
    y0 = max(top - int(head_h * 0.06), 0)
    y1 = min(head_end + int(head_h * SHOULDER_KEEP), gray.shape[0])

    print(f"head: y[{top}:{head_end}] x[{left}:{right}] -> frame y[{y0}:{y1}] x[{x0}:{x1}]")
    return gray[y0:y1, x0:x1]


def prepare(src: Path, dst: Path) -> None:
    im = Image.open(src).convert("RGB")
    arr = np.asarray(im)

    ring = detect_ring(arr)
    if ring is not None:
        cx, cy, radius = ring
        yy, xx = np.ogrid[: arr.shape[0], : arr.shape[1]]
        outside = (xx - cx) ** 2 + (yy - cy) ** 2 > radius**2
        arr = arr.copy()
        arr[outside] = 255
        box = (
            int(max(cx - radius, 0)),
            int(max(cy - radius, 0)),
            int(min(cx + radius, arr.shape[1])),
            int(min(cy + radius, arr.shape[0])),
        )
        im = Image.fromarray(arr).crop(box)
        print(f"ring detected: centre=({cx:.0f},{cy:.0f}) radius={radius:.0f} crop={box}")
    else:
        print("no ring detected, image used as is")

    gray = np.asarray(ImageOps.grayscale(im))
    bg_level = estimate_background(gray)
    print(f"estimated background level: {bg_level}")

    gray = flatten_background(gray, bg_level)
    gray = retexture_shadows(gray)
    gray = crop_to_head(gray)
    out = ImageOps.autocontrast(Image.fromarray(gray), cutoff=1)

    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    print(f"wrote {dst}: {out.size}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: prep_photo.py <source> [destination]")
    source = Path(sys.argv[1])
    target = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/portrait-prepped.png")
    prepare(source, target)
