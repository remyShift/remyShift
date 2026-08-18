# Generating the profile SVGs

**Never edit the SVG files by hand.** They are build output. The daily
workflow regenerates `contrib-heatmap.svg` and commits it, so any manual edit
there is reverted within hours, and `banner.svg` is overwritten the next time
`make_banner.py` runs. Change the source instead: prompt identity lives in
`USER` in `chassis.py`, identity rows in `ROWS` in `make_banner.py`.

Three SVGs, all self-contained: GitHub serves README images through its own
proxy, so an SVG cannot make any external request. System fonts, SMIL or
embedded CSS animations, nothing else.

## The calendar, automatic

Refreshed daily by `.github/workflows/update-profile-art.yml`. Nothing to do
by hand. To replay it locally:

```bash
pip install -r scripts/requirements.txt
python scripts/fetch_contributions.py remyShift data/contributions.json
python scripts/render_heatmap_svg.py data/contributions.json contrib-heatmap.svg
```

The fetcher scrapes the public HTML page, so no token is needed. In exchange
the markup can change: the script then exits with an error instead of writing
an empty calendar, and the workflow goes red.

The calendar reflects whatever GitHub publishes on the public profile page.
Private repository activity is included only while **Contribution settings ->
Private contributions** is enabled on the account; turn it off and the numbers
silently drop back to public-only. No code change either way.

## The banner, by hand

Portrait and identity panel share one screen, laid out like real neofetch
output. Content is the `ROWS` list at the top of `make_banner.py`. After
editing:

```bash
python scripts/make_banner.py data/portrait-prepped.png banner.svg
```

The panel carries its own prompt line, which is why the README has no heading
above it. Adding one would say the same thing twice.

## The portrait, once

Only needs re-preparing if the photo changes.

```bash
pip install -r scripts/requirements-portrait.txt
python scripts/prep_photo.py <photo.png> data/portrait-prepped.png
python scripts/make_banner.py data/portrait-prepped.png banner.svg
```

`prep_photo.py` detects a coloured ring around the subject, flattens the
uniform background and frames on the head. That last part matters: frame on
the bust and the shoulders are three times wider than the head, which makes
the face unreadable.

`--invert` on `make_banner.py` renders light ink on a dark screen, which
concentrates glyph density on the face and gives it more detail. Without the
flag, the default: dark ink on a light screen, sharper silhouette, softer
face. Match it to `THEME` in `palette.py` or the banner will not sit with the
calendar.

## Chassis

`chassis.py` draws the cream shell, the wine bezel and the recessed screen,
plus the prompt line. Modelled on `WineBorder.tsx` and `Screen.tsx` of the
portfolio, where the bezel is a filled wine block with the screen sitting
inside it, not a hairline stroke. All three generators call it, so widening
`BEZEL_W` once changes every panel.

Panel sizes are derived from their content, so changing `BEZEL_W` or `INSET`
changes the SVG dimensions. Banner and calendar have to keep the same width,
in the SVGs and in the `width` attributes of the root `README.md`.

## Palette

`palette.py`, taken from `tailwind.config.ts` of the remy-shift.dev portfolio.
All three generators import from it, so changing a colour in one place is
enough.

Two themes. Switch with `THEME = LIGHT` or `THEME = DARK`, then re-render all
three files (and add or drop `--invert` on the portrait to match).

`LIGHT` is the default because WINE is a dark colour: it works as ink on a
light screen and is unusable as a fill on a dark one, where its luminance
(0.165) falls below the empty cell. On `LIGHT` it is the peak of the ramp; on
`DARK` it only survives in the prompt line, on the cream shell.

Two rules any new ramp has to keep, both learned the hard way:

- Luminance moves strictly in one direction, climbing on dark, falling on
  light. Break it and a one-contribution day reads as emptier than a blank one.
- The empty level stays neutral and clearly separated from the screen,
  otherwise the grid stops reading as a calendar and looks like scattered dots.

Level 1 covers most days on an active account, so its colour sets the overall
impression far more than the peak does. That is why the light ramp starts
grey-brown rather than pale pink.
