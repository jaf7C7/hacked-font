# Hacked Font

Builds **Hacked**: Hack v3.003 with a few glyphs swapped for alternates from
[alt-hack](https://github.com/source-foundry/alt-hack). It installs alongside
the original Hack without name collisions.

## Build and install

```sh
./build.sh                      # builds the image if missing, then the fonts → dist/
./build.sh --rebuild-image      # refresh the image after changing Containerfile or the lock file
cp dist/*.ttf ~/.local/share/fonts/ && fc-cache -f
```

Needs only rootless podman on the host. Building the image is the only step that downloads
anything. The font build itself runs with `--network=none` in a throwaway container.

After a build the host keeps only `localhost/hacked-builder:latest` (about 630MB), the
`debian:trixie-slim` base image and `dist/*.ttf`.

## Files

| Path | Purpose |
|---|---|
| `hacked.conf` | Family name, chosen alternates (optionally limited to some styles with `@style,style`) and version note. Mounted at run time, so editing it needs no image rebuild. |
| `build.sh` | Host entry point. Removes the old image when it rebuilds, so only one copy is kept. |
| `Containerfile` | Debian trixie-slim, `ttfautohint`, a Python venv from the lock file, and the pinned Hack and alt-hack sources. |
| `container/build-font.sh` | Runs in the container: patches glyphs, strips stale hints, then runs fontmake, Hack's fixes, ttfautohint and the rename. |
| `container/rename.py` | Renames name IDs 1, 3, 4, 6, 16, 18 and 21 from Hack to Hacked, and appends the version note to ID 5. |
| `container/requirements.lock` | Pinned Python deps (fontmake 3.12.2, fonttools 4.67.0, …). |
| `.containerignore` | Keeps `src/`, `dist/` etc. out of the build context. |
| `specimen/` | Comparison page for every alt-hack alternate (see below). |
| `src/` | Host clones of Hack v3.003 and alt-hack, used only by the specimen generator. |

## Current picks

`u0030-diamond`, `u0033-flattop`, `u003C-wider` + `u003E-wider`, and `u0069-slab` with its 11
accented and Cyrillic siblings (`u00EC u00ED u00EE u00EF u0129 u012B u012D u012F u0131 u0456 u0457`).
The i-slab directories only make sense applied together. They're applied to Regular and Bold
only (`@regular,bold` in `hacked.conf`); Italic and Bold Italic keep Hack's default `i`.

## Decisions and why

- **Sources are pinned.** Hack is pinned to tag `v3.003`, and alt-hack to commit
  `9fab7328cfc208046cb7f3d713ec97a724d8219a`, the latest as of 2026-10-21.
- **ttfautohint is Debian's 1.8.4, not compiled from source.** Hack's
  `tools/scripts/install/ttfautohint-build.sh` compiles 1.7 (with freetype 2.8 and harfbuzz 1.5.0).
  The rule was to use Debian's package if it's the same version or newer, so Debian's is used.
  1.8.4 prints "`-w G` is deprecated, use `-a qsq`". It translates the flag itself, so Hack's
  original flags are kept as they are.
- **fontmake runs with `--production-names`.** Hack's hint files (`postbuild_processing/tt-hinting/*-TA.txt`)
  refer to glyphs as `uniXXXX`. The 2018 fontmake renamed glyphs that way by default. Current
  fontmake keeps the source names (`numbersign`, `zero`), and without this flag ttfautohint
  aborts with `invalid glyph name … uni0023`.
- **Stale hand-tuned hints are removed.** For each alternate, `build-font.sh` deletes the
  `uniXXXX` lines and the `# U+XXXX` heading from all four TA files, as alt-hack's README
  says to. With the current picks, only `uni0030` in `Hack-Regular-TA.txt` has any.
- **Python deps are pinned.** Hack's own build runs `pip install --upgrade fontmake` unpinned.
  To regenerate the lock, run `pip install fontmake && pip freeze` in a fresh trixie container,
  replace `container/requirements.lock`, then run `./build.sh --rebuild-image`.
- **Naming.** Pickers show only `Hacked`. The version string (name ID 5) also carries
  ttfautohint's settings plus `Hacked: 0-diamond 3-flattop <>-wider i-slab(upright)`, so an installed
  copy records what it contains.
- **TTF only.** No woff or woff2.

## Known limitations

- **Superscripts and fractions keep Hack's default shapes.** `³ ⁰ ¾ ⅓` are separate glyphs,
  and alt-hack has no alternates for them. This was accepted when choosing the picks.
- **Hinting differs from official Hack 3.003** (compared against the release TTFs on 2026-10-22):
  - **Identical:** the ttfautohint settings, the control values (`cvt`) and the
    rendering-mode table (`gasp`).
  - **Different:** ttfautohint 1.7 → 1.8.4 changes the hint function library (`fpgm`/`prep`,
    about 160 bytes larger) and the per-glyph hint code in about 98% of glyphs. The byte
    comparison can't tell real hinting changes from renumbered code.
  - **Outlines:** about 30% of unswapped glyphs have different points from fontmake 3.12's
    curve conversion. Contours, point counts and bounding boxes are identical, and the
    largest area change is 0.29%.
  - **Visual impact:** not yet measured by rasterizing. Any effect is limited to small sizes,
    since hinting does nothing at high DPI.
- **Verification so far:**
  - `fc-scan` reports family `Hacked` for all four styles.
  - Each swapped glyph's outline extents match the alt-hack source.
  - The rendered fonts have not been checked by eye yet.

## Specimen page

`specimen/gen.py` draws every alt-hack alternate next to Hack's default, straight from the
`.glif` sources, so no font build is needed. Regenerate it with:

```sh
python3 -I specimen/gen.py src/hack src/alt-hack specimen/alt-hack-specimen.html
```

It's published privately at https://claude.ai/artifact/WjzuoyABYZMT98XLb3v1N1.

alt-hack's 27 glyph directories make 12 distinct options:
- 4 zeros: backslash, diamond, dotted and forwardslash.
- 2 parenthesis styles: curved and rounder.
- One alternate each for `1` (noslab), `3` (flattop), `<>` (wider), `[]` (oldv3) and `f` (knife).
- The i-slab group.
