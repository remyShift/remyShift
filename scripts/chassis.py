"""Shared Game Boy chassis: cream shell, wine bezel, recessed screen.

Modelled on WineBorder.tsx and Screen.tsx of the remy-shift.dev portfolio,
where the bezel is a filled wine block with the grey screen sitting inside it
at 94% width, not a hairline stroke. All three generators build the same
chassis, so it lives here rather than being copied three times and drifting.

Geometry, outermost first:

    SHELL_PAD  cream margin
    BEZEL_W    wine band
    INSET      breathing room between the screen edge and the content
"""

from palette import BEZEL_INK, MONO, SCREEN, SHELL, WINE

# Prompt identity, single source for every panel. Editing the generated SVGs
# by hand does not survive: the daily workflow regenerates the calendar from
# render_heatmap_svg.py and commits the revert.
USER = "remyshift@github"

HEADER_H = 30.0
SHELL_PAD = 14.0
BEZEL_W = 13.0
INSET = 10.0

SHELL_RADIUS = 16.0
BEZEL_RADIUS = 12.0
SCREEN_RADIUS = 7.0

# Approximates the portfolio's `inset 0 0 0.6rem 0.22rem` on the screen: an
# inner stroke is cheaper than an SVG filter and survives any renderer.
SHADOW_WIDTH = 3.0
SHADOW_OPACITY = 0.18


def canvas_size(content_w: float, content_h: float) -> tuple[float, float]:
    """Full SVG size needed to wrap a content box in the chassis."""
    edge = INSET + BEZEL_W + SHELL_PAD
    return content_w + edge * 2, content_h + edge * 2 + HEADER_H


def content_origin() -> tuple[float, float]:
    """Top-left corner of the content area, inside the screen."""
    return SHELL_PAD + BEZEL_W + INSET, SHELL_PAD + HEADER_H + BEZEL_W + INSET


def prompt(command: str) -> str:
    """Shell prompt line shown above each panel."""
    return f"{USER} ~ $ {command}"


def styles() -> list[str]:
    """CSS rules the chassis needs. Callers append their own."""
    return [
        f".t{{font-family:{MONO}}}",
        f".hdr{{font-size:11px;fill:{WINE};letter-spacing:.06em}}",
    ]


def build(width: float, height: float, prompt: str) -> list[str]:
    """SVG fragments for shell, bezel, screen and prompt line."""
    bezel_x = SHELL_PAD
    bezel_y = SHELL_PAD + HEADER_H
    bezel_w = width - SHELL_PAD * 2
    bezel_h = height - bezel_y - SHELL_PAD

    screen_x = bezel_x + BEZEL_W
    screen_y = bezel_y + BEZEL_W
    screen_w = bezel_w - BEZEL_W * 2
    screen_h = bezel_h - BEZEL_W * 2

    half = SHADOW_WIDTH / 2
    return [
        f'<rect width="{width:.0f}" height="{height:.0f}" '
        f'rx="{SHELL_RADIUS}" fill="{SHELL}"/>',
        f'<rect x="{bezel_x:.1f}" y="{bezel_y:.1f}" '
        f'width="{bezel_w:.1f}" height="{bezel_h:.1f}" '
        f'rx="{BEZEL_RADIUS}" fill="{WINE}"/>',
        f'<rect x="{screen_x:.1f}" y="{screen_y:.1f}" '
        f'width="{screen_w:.1f}" height="{screen_h:.1f}" '
        f'rx="{SCREEN_RADIUS}" fill="{SCREEN}"/>',
        f'<rect x="{screen_x + half:.1f}" y="{screen_y + half:.1f}" '
        f'width="{screen_w - SHADOW_WIDTH:.1f}" height="{screen_h - SHADOW_WIDTH:.1f}" '
        f'rx="{SCREEN_RADIUS}" fill="none" stroke="{BEZEL_INK}" '
        f'stroke-width="{SHADOW_WIDTH}" stroke-opacity="{SHADOW_OPACITY}"/>',
        f'<text class="t hdr" x="{SHELL_PAD:.1f}" y="20">{prompt}</text>',
    ]
