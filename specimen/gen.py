"""Generate an HTML specimen comparing Hack's default glyphs with alt-hack alternates.

Usage: python3 -I gen.py <hack-repo> <alt-hack-repo> <out.html>

Draws outlines straight from the UFO .glif sources, so no font build is needed.
"""
import html
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

STYLES = [("Regular", "regular"), ("Bold", "bold"), ("Italic", "italic"), ("BoldItalic", "bolditalic")]
STYLE_LABEL = {"Regular": "Regular", "Bold": "Bold", "Italic": "Italic", "BoldItalic": "Bold Italic"}
ADV = 1233
ASC, DESC = 1556, -492  # from fontinfo.plist; unitsPerEm 2048

# Each slot is a set of code points swapped together; alternates in a slot are mutually exclusive.
SLOTS = [
    dict(key="zero", title="Zero", cps=["0030"], hero="0", sample="0O 0o 00:30 0x00FF 10.05 O0"),
    dict(key="one", title="One", cps=["0031"], hero="1", sample="1lI| 1001 l1I il1 x[1]"),
    dict(key="three", title="Three", cps=["0033"], hero="3", sample="1234567890 33.3 0x3E8"),
    dict(key="parens", title="Parentheses", cps=["0028", "0029"], hero="()",
         sample="fn(a, (b + c)) if (x) {}"),
    dict(key="angles", title="Angle brackets", cps=["003C", "003E"], hero="<>",
         sample="a <= b < c -> Vec<T> <br/>"),
    dict(key="brackets", title="Square brackets", cps=["005B", "005D"], hero="[]",
         sample="arr[i][j] = [0, [1]]"),
    dict(key="f", title="Lowercase f", cps=["0066"], hero="f", sample="if fifo def off() ff"),
    dict(key="i", title="Lowercase i family",
         cps=["0069", "00EC", "00ED", "00EE", "00EF", "0129", "012B", "012D", "012F", "0131", "0456", "0457"],
         hero="iìíîïı", sample="if i in list: ìíîï ĩīĭį ı іїi"),
]


def glif_path(fn):
    root = ET.parse(fn).getroot()
    out = []
    for c in root.iter("contour"):
        pts = [(float(p.get("x")), float(p.get("y")), p.get("type") or "offcurve") for p in c.iter("point")]
        if not pts:
            continue
        on = [i for i, p in enumerate(pts) if p[2] != "offcurve"]
        if not on:
            continue
        closed = pts[0][2] != "move"
        if closed:
            s = on[0]
            pts = pts[s + 1:] + pts[:s + 1]
            start = pts[-1]
        else:
            start, pts = pts[0], pts[1:]
        d = [f"M{start[0]:g} {start[1]:g}"]
        off = []
        for x, y, t in pts:
            if t == "offcurve":
                off.append((x, y))
                continue
            if t == "line" or (t in ("curve", "qcurve") and not off):
                d.append(f"L{x:g} {y:g}")
            elif t == "curve" and len(off) == 2:
                d.append(f"C{off[0][0]:g} {off[0][1]:g} {off[1][0]:g} {off[1][1]:g} {x:g} {y:g}")
            elif t == "qcurve" or t == "curve":
                # quadratic (or odd cubic) run: implied on-curve midpoints
                for j, (ox, oy) in enumerate(off):
                    if j + 1 < len(off):
                        nx, ny = (ox + off[j + 1][0]) / 2, (oy + off[j + 1][1]) / 2
                    else:
                        nx, ny = x, y
                    d.append(f"Q{ox:g} {oy:g} {nx:g} {ny:g}")
            off = []
        if closed:
            d.append("Z")
        out.append("".join(d))
    return "".join(out)


def cmap(glyph_dir):
    m = {}
    for fn in glyph_dir.glob("*.glif"):
        for u in ET.parse(fn).getroot().iter("unicode"):
            m.setdefault(int(u.get("hex"), 16), fn)
    return m


def main(hack, alt, out):
    hack, alt = Path(hack), Path(alt)
    cmaps = {s: cmap(hack / f"source/Hack-{s}.ufo/glyphs") for s, _ in STYLES}
    variants = sorted(p.name for p in (alt / "glyphs").iterdir() if p.is_dir())
    defs = {}  # id -> path d

    def gid(style, cp, var=None):
        return f"{style}-{cp:04X}" + (f"-{var}" if var else "")

    def ensure(style, cp, var=None):
        i = gid(style, cp, var)
        if i not in defs:
            if var:
                low = dict(STYLES)[style]
                fn = next((alt / "glyphs" / f"u{cp:04X}-{var}" / low).glob("*.glif"))
            else:
                fn = cmaps[style].get(cp)
                if fn is None:
                    return None
            defs[i] = glif_path(fn)
        return i

    def run(text, style, swaps, cls_cps):
        """SVG for a line of text; swaps maps cp->variant; cls_cps are highlighted."""
        uses = []
        for n, ch in enumerate(text):
            cp = ord(ch)
            if ch == " ":
                continue
            i = ensure(style, cp, swaps.get(cp))
            if i is None:
                continue
            cls = ' class="hl"' if cp in cls_cps else ""
            uses.append(f'<use href="#{i}" x="{n * ADV}"{cls}/>')
        w = len(text) * ADV
        return (f'<svg viewBox="0 {-ASC} {w} {ASC - DESC}" style="--n:{len(text)}" aria-label="{html.escape(text)}">'
                f'<g transform="scale(1,-1)">{"".join(uses)}</g></svg>')

    def glyph_cell(text, style, swaps):
        uses = []
        for n, ch in enumerate(text):
            cp = ord(ch)
            i = ensure(style, cp, swaps.get(cp))
            uses.append(f'<use href="#{i}" x="{n * ADV}"/>')
        # baseline + x-height + cap-height guides
        w = len(text) * ADV
        guides = "".join(f'<line x1="0" x2="{w}" y1="{y}" y2="{y}"/>' for y in (0, 1120, 1493))
        return (f'<svg class="g" viewBox="0 {-ASC} {w} {ASC - DESC}" style="--n:{len(text)}">'
                f'<g transform="scale(1,-1)"><g class="guides">{guides}</g>{"".join(uses)}</g></svg>')

    sections = []
    toc = []
    for slot in SLOTS:
        cps = {int(c, 16) for c in slot["cps"]}
        prefixes = tuple(f"u{c}-" for c in slot["cps"])
        names = sorted({v.split("-", 1)[1] for v in variants if v.startswith(prefixes)})
        # check each alternate covers every cp in the slot
        opts = [("default", None)]
        for nm in names:
            have = [c for c in slot["cps"] if (alt / "glyphs" / f"u{c}-{nm}").is_dir()]
            opts.append((nm, have))
        cols = []
        for nm, have in opts:
            swaps = {} if have is None else {int(c, 16): nm for c in have}
            cells = "".join(
                f'<div class="cell"><span class="sl">{STYLE_LABEL[s]}</span>{glyph_cell(slot["hero"], s, swaps)}</div>'
                for s, _ in STYLES)
            samples = "".join(
                f'<div class="sample" data-style="{s}">{run(slot["sample"], s, swaps, cps)}</div>'
                for s, _ in STYLES)
            if have is None:
                head = '<span class="opt">Hack default</span><code>v3.003</code>'
            else:
                ids = " + ".join(f"u{c}-{nm}" for c in have)
                head = f'<span class="opt">{html.escape(nm)}</span><code>{ids}</code>'
            cls = "col def" if have is None else "col"
            cols.append(f'<figure class="{cls}"><figcaption>{head}</figcaption>'
                        f'<div class="cells">{cells}</div>{samples}</figure>')
        cpl = " ".join(f"U+{c}" for c in slot["cps"]) if len(slot["cps"]) <= 2 else \
            f"U+{slot['cps'][0]} and {len(slot['cps']) - 1} accented forms"
        n_alt = len(opts) - 1
        sections.append(
            f'<section id="{slot["key"]}"><header><h2>{slot["title"]}</h2>'
            f'<p class="meta"><span>{cpl}</span><span>{n_alt} alternate{"s" if n_alt != 1 else ""}</span></p></header>'
            f'<div class="cols" style="--cols:{len(opts)}">{"".join(cols)}</div></section>')
        toc.append(f'<a href="#{slot["key"]}">{html.escape(slot["hero"][:2])}<span>{slot["title"]}</span></a>')

    total_builds = sum(1 for s in sections) and sum(
        len({v.split("-", 1)[1] for v in variants if v.startswith(tuple(f"u{c}-" for c in sl["cps"]))})
        for sl in SLOTS)
    defs_svg = "".join(f'<path id="{k}" d="{v}"/>' for k, v in sorted(defs.items()))
    tpl = (Path(__file__).parent / "template.html").read_text()
    page = (tpl.replace("{{DEFS}}", defs_svg)
               .replace("{{SECTIONS}}", "\n".join(sections))
               .replace("{{TOC}}", "".join(toc))
               .replace("{{NBUILDS}}", str(total_builds))
               .replace("{{NDIRS}}", str(len(variants))))
    Path(out).write_text(page)
    print(f"wrote {out}: {len(defs)} glyph outlines, {total_builds} alternates, {len(variants)} alt-hack dirs")


if __name__ == "__main__":
    main(*sys.argv[1:4])
