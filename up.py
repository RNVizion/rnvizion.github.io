#!/usr/bin/env python3
"""The share-image generators draw the brand's own font files; font.sh retires.
Built from: rnvizion.github.io@34de289 · rnv-brand@db7dba0 · Brand Book decision #37 ·
the operator's request of 2026-10-20 that font.sh stop fetching from google/fonts.
Run from the site repo root. All or nothing: every edit is checked before any file
is written, and a second run refuses.

What it does:
  1. generate_og.py, generate_site_og.py, generate_project_card.py read the woff2
     files in assets/webfonts/, the copy of rnv-brand's engine/fonts/ the site
     already serves and the type check already compares. OG_FONT_DIR still overrides.
  2. load_font() stops with the font's name instead of drawing a default face, and
     stops if a variable font has none of the weights asked for.
  3. scripts/font.sh is deleted, with its step in build-og.yml and its call in the
     devcontainer. build-og.yml watches assets/webfonts/*.woff2 instead, so a new
     copy of the brand's fonts regenerates the images.
  4. .gitignore keeps assets/fonts/, so a checkout still holding the old TTFs never
     commits them, with its comment saying why.
Checked before it was handed over: every share image on the site renders
pixel-identical with these files and with font.sh's TTFs."""
import pathlib, sys

FILES = {
    '"BricolageGrotesque.ttf"': '"bricolage-grotesque-latin-opsz-normal.woff2"',
    '"JetBrainsMono.ttf"': '"jetbrains-mono-latin-500-normal.woff2"',
    '"Montserrat.ttf"': '"montserrat-latin-900-normal.woff2"',
}
COUNTS = {  # how many times each generator names each file today
    "scripts/generate_og.py": {'"BricolageGrotesque.ttf"': 2, '"JetBrainsMono.ttf"': 1, '"Montserrat.ttf"': 1},
    "scripts/generate_site_og.py": {'"BricolageGrotesque.ttf"': 2, '"JetBrainsMono.ttf"': 5, '"Montserrat.ttf"': 1},
    "scripts/generate_project_card.py": {'"BricolageGrotesque.ttf"': 2, '"JetBrainsMono.ttf"': 3, '"Montserrat.ttf"': 1},
}
OLD_LOAD = '''def load_font(path, size, weights=("SemiBold", "Bold", "Medium")):
    try:
        font = ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()
    for name in weights:{c}
        try:
            font.set_variation_by_name(name)
            break
        except Exception:
            continue
    return font
'''
OLD_LOAD_VARIANTS = [OLD_LOAD.format(c="  # variable fonts: pick a heavier instance if available"), OLD_LOAD.format(c="")]
NEW_LOAD = '''def load_font(path, size, weights=("SemiBold", "Bold", "Medium")):
    """The brand's own font file, at the first weight asked for that it has.

    Stops by name rather than drawing a default face: a share image in the
    wrong face is a published error that nobody is told about.
    """
    try:
        font = ImageFont.truetype(str(path), size)
    except Exception as exc:
        sys.exit(f"cannot load {path}: {exc}. The generators draw the brand's own "
                 f"files from assets/webfonts/ (or OG_FONT_DIR).")
    try:
        names = [n.decode() if isinstance(n, bytes) else n
                 for n in font.get_variation_names()]
    except Exception:
        return font   # a single-weight file is the weight it was cut at
    for name in weights:
        if name in names:
            font.set_variation_by_name(name)
            return font
    sys.exit(f"{path} has none of the weights {weights}; it offers {names}")
'''
FONT_DIR_OLD = 'FONT_DIR = Path(os.environ.get("OG_FONT_DIR", REPO / "assets" / "fonts"))'
FONT_DIR_NEW = 'FONT_DIR = Path(os.environ.get("OG_FONT_DIR", REPO / "assets" / "webfonts"))'
DOCS = {
    "scripts/generate_og.py": (
        "Fonts live in assets/fonts/ (override with OG_FONT_DIR). Drop these three there:\n"
        "  BricolageGrotesque.ttf   (display)   Montserrat.ttf     (the mark)\n"
        "  JetBrainsMono.ttf        (labels, captions, footer)\n"
        "If a font is missing the script still renders, just with a default face.\n",
        "Fonts are the brand's own woff2 files in assets/webfonts/, the copy of rnv-brand's\n"
        "engine/fonts/ the site serves (override the folder with OG_FONT_DIR): Bricolage\n"
        "Grotesque for the title, Montserrat Black for the mark, JetBrains Mono for labels.\n"
        "A missing or unreadable font stops the script with its name.\n"),
    "scripts/generate_site_og.py": (
        "Fonts come from assets/fonts/ (override with OG_FONT_DIR); run ./scripts/font.sh first.\n",
        "Fonts are the brand's own woff2 files in assets/webfonts/ (override with OG_FONT_DIR).\n"),
    "scripts/generate_project_card.py": (
        "overwritten. Fonts come from assets/fonts/ (override with OG_FONT_DIR); run\n./scripts/font.sh first.\n",
        "overwritten. Fonts are the brand's own woff2 files in assets/webfonts/ (override\nwith OG_FONT_DIR).\n"),
}
OTHER = {
    ".github/workflows/build-og.yml": [
        ('      - "scripts/font.sh"\n', '      - "assets/webfonts/*.woff2"\n'),
        ("      - name: Fetch brand fonts\n        run: bash scripts/font.sh\n\n", ""),
        ("          # assets/fonts/ is gitignored, so scripts/font.sh's downloads are never staged\n", ""),
    ],
    ".devcontainer/devcontainer.json": [
        ('"postCreateCommand": "pip install --user Pillow qrcode beautifulsoup4 lxml && bash scripts/font.sh",',
         '"postCreateCommand": "pip install --user Pillow qrcode beautifulsoup4 lxml",'),
    ],
    ".gitignore": [
        ("# fetched by scripts/font.sh; never commit\nassets/fonts/\n",
         "# Held scripts/font.sh's TTFs until 2026-10-20; the generators now read\n"
         "# assets/webfonts/. Kept so a checkout that still holds the TTFs never commits them.\n"
         "assets/fonts/\n"),
    ],
}

def refuse(msg):
    sys.exit("refused, nothing written: " + msg + " (already applied, or the file moved: re-read it)")

if not pathlib.Path("scripts/font.sh").exists():
    refuse("scripts/font.sh is not here")
for f in ("bricolage-grotesque-latin-opsz-normal.woff2", "jetbrains-mono-latin-500-normal.woff2", "montserrat-latin-900-normal.woff2"):
    if not pathlib.Path("assets/webfonts", f).is_file():
        refuse(f"assets/webfonts/{f} is missing")

out = {}
for path, counts in COUNTS.items():
    s = pathlib.Path(path).read_text(encoding="utf-8")
    for old, n in counts.items():
        if s.count(old) != n:
            refuse(f"{path}: expected {n} of {old}, found {s.count(old)}")
        s = s.replace(old, FILES[old])
    if s.count(FONT_DIR_OLD) != 1:
        refuse(f"{path}: FONT_DIR line")
    s = s.replace(FONT_DIR_OLD, FONT_DIR_NEW)
    hits = [v for v in OLD_LOAD_VARIANTS if s.count(v) == 1]
    if len(hits) != 1:
        refuse(f"{path}: load_font is not in a known shape")
    s = s.replace(hits[0], NEW_LOAD)
    old_doc, new_doc = DOCS[path]
    if s.count(old_doc) != 1:
        refuse(f"{path}: docstring font line")
    s = s.replace(old_doc, new_doc)
    if "load_default" in s or ".ttf\"" in s or "font.sh" in s:
        refuse(f"{path}: a reference to the old fonts is left")
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
pathlib.Path("scripts/font.sh").unlink()
print(f"ok: {len(out)} files edited, scripts/font.sh deleted; now run the three generators and the tests")
