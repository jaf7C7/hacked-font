#!/bin/bash
# Runs inside the builder container. Patches Hack with alt-hack glyphs, builds,
# hints and renames the TTFs, then writes them to /out.
#
# Mirrors Hack v3.003's build-ttf.sh, using ttfautohint from PATH.
set -euo pipefail

CONF=/config/hacked.conf
SRC_HACK=/opt/src/hack
SRC_ALT=/opt/src/alt-hack
OUT=/out
WORK=/tmp/hack

# shellcheck source=../hacked.conf
source "$CONF"

STYLES=(Regular Bold Italic BoldItalic)
# ttfautohint -H (x-height increase limit) per style, from Hack's build-ttf.sh
declare -A TA_H=([Regular]=181 [Bold]=260 [Italic]=145 [BoldItalic]=265)

echo "== Copying Hack source"
rm -rf "$WORK"
cp -a "$SRC_HACK" "$WORK"
cd "$WORK"

echo "== Applying alternates"
for alt in "${ALTERNATES[@]}"; do
    [[ -d "$SRC_ALT/glyphs/$alt" ]] || { echo "Unknown alternate: $alt" >&2; exit 1; }
    for style in "${STYLES[@]}"; do
        dest="source/Hack-$style.ufo/glyphs"
        for glif in "$SRC_ALT/glyphs/$alt/${style,,}"/*.glif; do
            # alt-hack files replace existing ones; a new file would mean a path mismatch.
            [[ -f "$dest/${glif##*/}" ]] || { echo "No existing $dest/${glif##*/} to replace" >&2; exit 1; }
            cp "$glif" "$dest/"
        done
    done
    # Drop hand-tuned hints for the replaced code point; they target the old outline.
    cp_hex="${alt%%-*}"          # u0030
    cp_hex="${cp_hex#u}"         # 0030
    sed -i -e "/^uni${cp_hex} /d" -e "/^# U+${cp_hex} /d" postbuild_processing/tt-hinting/*-TA.txt
    echo "   $alt"
done

echo "== Compiling (fontmake $(fontmake --version 2>&1 | tail -1))"
for style in "${STYLES[@]}"; do
    # --production-names: rename glyphs to uniXXXX, as the 2018 fontmake did by
    # default. Hack's hint files (tt-hinting/*-TA.txt) refer to glyphs by those names.
    fontmake -u "source/Hack-$style.ufo" -o ttf --output-dir master_ttf --production-names
done

echo "== Post-build fixes"
python postbuild_processing/fixes/fix-dsig.py master_ttf/*.ttf
python postbuild_processing/fixes/fix-fstype.py master_ttf/*.ttf

echo "== Hinting ($(ttfautohint --version | head -1))"
mkdir -p master_ttf/hinted
for style in "${STYLES[@]}"; do
    ttfautohint -l 6 -r 50 -x 10 -H "${TA_H[$style]}" -D latn -f latn -w G -W -t -X "" -I \
        -m "postbuild_processing/tt-hinting/Hack-$style-TA.txt" \
        "master_ttf/Hack-$style.ttf" "master_ttf/hinted/Hack-$style.ttf"
done

echo "== Renaming to $FAMILY"
mkdir -p "$OUT"
for style in "${STYLES[@]}"; do
    python /work/container/rename.py "master_ttf/hinted/Hack-$style.ttf" "$OUT/$FAMILY-$style.ttf" \
        "$FAMILY" "$VERSION_NOTE"
done
echo "== Done"
