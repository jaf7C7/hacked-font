"""Rename a Hack TTF to a new family so it installs alongside Hack.

Usage: rename.py <in.ttf> <out.ttf> <family> <version-note>

Replaces the word "Hack" in the identifying name records (family, full name,
PostScript name, unique ID, typographic family) and appends <version-note>
to the version string. Copyright, license and designer records are left alone.
"""
import re
import sys

from fontTools.ttLib import TTFont

# 1 family, 3 unique ID, 4 full name, 6 PostScript name, 16 typographic family,
# 18 compatible full name, 21 WWS family
RENAME_IDS = {1, 3, 4, 6, 16, 18, 21}


def main(src, dst, family, note):
    font = TTFont(src)
    ps_family = family.replace(" ", "")
    for rec in font["name"].names:
        text = rec.toUnicode()
        if rec.nameID in RENAME_IDS:
            repl = ps_family if rec.nameID == 6 else family
            new = re.sub(r"\bHack\b", repl, text)
        elif rec.nameID == 5 and note:
            new = f"{text}; {note}"
        else:
            continue
        rec.string = new
    font.save(dst)
    for rec in font["name"].names:
        if rec.platformID == 3 and rec.nameID in RENAME_IDS | {5}:
            print(f"   {dst.rsplit('/', 1)[-1]}  name {rec.nameID:>2}: {rec.toUnicode()}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
