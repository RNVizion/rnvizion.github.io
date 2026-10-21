#!/usr/bin/env python3
"""The share-image generators stop by name on a character their font cannot draw.
Built from: rnvizion.github.io@1ecec62 · Brand Infrastructure's note of 2026-10-20
(BRAND_TYPE.md rev 16) · the operator's ruling of 2026-10-20 in the brand chat.
Run from the site repo root. All or nothing: every edit is checked before any file
is written, and a second run refuses.

Why: since beeeb34 each generator loads the Latin file of its face. A browser falls
back to the Latin Extended file for a character the first lacks; Pillow draws from
one file and cannot, so a title carrying an arrow, a bullet, a check mark, or a
letter such as ł, š or ā would publish a missing-glyph box and report success.

What it does:
  1. generate_og.py, generate_site_og.py, generate_project_card.py: every string
     the script draws is checked against the cmap of the file it is drawn in, and
     a character with no glyph stops the run with the file, the character and the
     text. Text drawn with no font stops it too, since Pillow would draw its own.
     Whitespace is not checked. Measuring text is not drawing it, so textlength()
     is left alone.
  2. build-og.yml and the devcontainer install fonttools and brotli beside Pillow:
     fontTools reads the cmap, and brotli is how it opens a woff2 file.
Checked before it was handed over: all 19 share images render pixel-identical with
the guard on; a post titled with an arrow, and one with "ł", stop by name and write
nothing; text drawn with no font stops by name."""
import pathlib, sys

GENS = ["scripts/generate_og.py", "scripts/generate_site_og.py", "scripts/generate_project_card.py"]
IMPORT_OLD = "from PIL import Image, ImageDraw, ImageFont\n"
IMPORT_NEW = "from PIL import Image, ImageDraw, ImageFont\nfrom fontTools.ttLib import TTFont\n"
ANCHOR = '    sys.exit(f"{path} has none of the weights {weights}; it offers {names}")\n'
GUARD = ANCHOR + '''

_CMAPS = {}


def require_glyphs(text, font):
    """Stop by name if the font cannot draw a character of text.

    The generators load the Latin file of each face, and Pillow draws from that
    file alone, so a character it lacks becomes a missing-glyph box in a published
    image. Whitespace is not checked.
    """
    path = getattr(font, "path", None)
    if path is None:
        sys.exit(f"drew {text!r} with no font; the generators draw only the brand's "
                 f"files from assets/webfonts/ (or OG_FONT_DIR).")
    cmap = _CMAPS.get(path)
    if cmap is None:
        cmap = _CMAPS[path] = TTFont(path).getBestCmap()
    missing = sorted({c for c in text if not c.isspace() and ord(c) not in cmap})
    if missing:
        sys.exit(f"{Path(path).name} has no glyph for {' '.join(missing)} "
                 f"({', '.join(f'U+{ord(c):04X}' for c in missing)}) in {text!r}. "
                 f"Change the text, or draw it from a file that has the glyph.")


_draw_text = ImageDraw.ImageDraw.text


def _checked_text(self, xy, text, fill=None, font=None, *args, **kwargs):
    require_glyphs(text, font)
    return _draw_text(self, xy, text, fill, font, *args, **kwargs)


ImageDraw.ImageDraw.text = _checked_text   # every string this script draws
'''
DOCS = {
    "scripts/generate_og.py": (
        "A missing or unreadable font stops the script with its name.\n",
        "A missing or unreadable font stops the script with its name, and so does a\n"
        "character the font has no glyph for: these are the Latin files, and Pillow has\n"
        "no fallback.\n"),
    "scripts/generate_site_og.py": (
        "Fonts are the brand's own woff2 files in assets/webfonts/ (override with OG_FONT_DIR).\n",
        "Fonts are the brand's own woff2 files in assets/webfonts/ (override with OG_FONT_DIR).\n"
        "A character the font has no glyph for stops the script with its name.\n"),
    "scripts/generate_project_card.py": (
        "with OG_FONT_DIR).\n\"\"\"\n",
        "with OG_FONT_DIR). A character the font has no glyph for stops the script with\nits name.\n\"\"\"\n"),
}
OTHER = {
    ".github/workflows/build-og.yml": [
        ("      - name: Install Pillow\n        run: pip install Pillow\n",
         "      - name: Install Pillow and fontTools\n        run: pip install Pillow fonttools brotli\n"),
    ],
    ".devcontainer/devcontainer.json": [
        ('"postCreateCommand": "pip install --user Pillow qrcode beautifulsoup4 lxml",',
         '"postCreateCommand": "pip install --user Pillow fonttools brotli qrcode beautifulsoup4 lxml",'),
    ],
}


def refuse(msg):
    sys.exit("refused, nothing written: " + msg + " (already applied, or the file moved: re-read it)")


out = {}
for path in GENS:
    s = pathlib.Path(path).read_text(encoding="utf-8")
    if "fontTools" in s or "require_glyphs" in s:
        refuse(f"{path} already carries the guard")
    for old, new in ((IMPORT_OLD, IMPORT_NEW), (ANCHOR, GUARD), DOCS[path]):
        if s.count(old) != 1:
            refuse(f"{path}: expected 1 of {old.strip()[:60]!r}, found {s.count(old)}")
        s = s.replace(old, new)
    compile(s, path, "exec")
    out[path] = s
for path, edits in OTHER.items():
    s = pathlib.Path(path).read_text(encoding="utf-8")
    for old, new in edits:
        if s.count(old) != 1:
            refuse(f"{path}: expected 1 of {old.strip()[:60]!r}, found {s.count(old)}")
        s = s.replace(old, new)
    out[path] = s

for path, s in out.items():
    pathlib.Path(path).write_text(s, encoding="utf-8")
print(f"ok: {len(out)} files edited; install fonttools and brotli, then run the three generators")
