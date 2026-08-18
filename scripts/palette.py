"""Single source of colours for the three profile SVGs.

Taken from tailwind.config.ts of the remy-shift.dev portfolio, so the GitHub
profile and the site tell the same story. All three generators import from
here: without it the colours drift from one file to the next.

Two themes, because WINE decides the answer. WINE is a dark colour: it works
as ink on a light screen and is unusable as a fill on a dark one, where its
luminance (0.165) sits below the empty cell and barely above the screen. On
the light theme it becomes the peak of the ramp, at full strength. On the dark
theme it survives only in the prompt line, on the cream shell.
"""

# Chassis, shared by both themes.
SHELL = "#F8E9D9"      # cream
BEZEL_INK = "#2A2A2A"  # screen inner shadow, see Screen.tsx
BROWN = "#726456"      # topBrown
SAND = "#C6AF87"
WINE = "#5C131D"

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# Two hard constraints on every ramp, both learned the hard way:
#
# 1. Luminance moves strictly in one direction. On dark it climbs, on light it
#    falls. Break it and a one-contribution day reads as emptier than a blank
#    one, which is what putting raw WINE on the dark screen did.
# 2. The empty level stays neutral and clearly separated from the screen,
#    otherwise the grid stops reading as a calendar and looks like scattered
#    dots.

DARK = {
    "screen": "#2A2723",
    "ink": "#CFC7B8",
    "ink_dim": "#8A8172",
    "key": SAND,
    # Game Boy DMG green, hue ~85 degrees. Climbing: .24 .28 .40 .53 .68
    "levels": ["#443D34", "#33582D", "#497F2A", "#74A522", "#A9C932"],
}

LIGHT = {
    "screen": "#D8D5D0",
    "ink": "#3D1219",
    "ink_dim": "#7A7169",
    "key": WINE,
    # Grey-brown at the low levels, WINE reserved for the peaks. Level 1
    # covers most days, so a pale pink there would make the whole calendar
    # read pink instead of burgundy. Falling: .78 .66 .50 .32 .17
    "levels": ["#C8C4BE", "#ADA69E", "#8E7A78", "#7A4048", WINE],
}

THEME = LIGHT

SCREEN = THEME["screen"]
INK = THEME["ink"]
INK_DIM = THEME["ink_dim"]
KEY = THEME["key"]
LEVELS = THEME["levels"]

# The ASCII portrait needs both, since --invert picks the other one.
SCREEN_DARK, INK_LIGHT = DARK["screen"], DARK["ink"]
SCREEN_LIGHT, INK_DARK = LIGHT["screen"], LIGHT["ink"]
