#!/usr/bin/env python3
"""
generate_project_card.py — render a card image for a project that has no UI to
screenshot (an MCP server, an agent loop, a library).

Companion to generate_og.py: same brand palette, same faces, same wordmark, but
sized 4:3 to match the .project-image container on the homepage rather than the
1200x630 of an Open Graph share image.

SOURCE OF TRUTH
Reads index.html and finds the <article class="project"> whose <img src> points
at the card being generated, then pulls every value from that markup, the same
way generate_card.py pulls from a post:
  label <- <div class="project-number">   e.g. "04 / AGENTS"
  title <- <h3>                           e.g. "RNV Publishing Agent"
  tags  <- <span class="tag">             up to five, rendered as pills
Nothing is hand-copied, so the card can never drift from the page.

SLUG VALIDATION
A project article carries two independent references to the same project: the
image filename and the GitHub link. They must agree, because the house rule is
that an asset is named for its repo. So assets/rnv-color-mcp.png must sit in the
article that links to github.com/RNVizion/rnv-color-mcp.

That cross-check is what catches typos. A misspelled filename would otherwise be
invisible: the card generates, the tile looks fine, and the wrong name lives on
forever. Instead it is a hard error and the run stops.

Two deliberate exemptions:
  - images outside assets/ root (e.g. assets/brand/aiii-og.png) are reuse of an
    existing brand asset, not a project card; skipped entirely
  - an article with no github.com/RNVizion link cannot be cross-checked; it is
    reported as unverified and still rendered

USAGE (run from the repo root)
  python scripts/generate_project_card.py --check          # validate only
  python scripts/generate_project_card.py --all-missing    # validate, then fill gaps
  python scripts/generate_project_card.py rnv-color-mcp --force

  # standalone, no index.html lookup:
  python scripts/generate_project_card.py my-thing \\
      --title "RNV Something" --label "10 / TOOLS" --tags "Python,CLI"

Existing files are left alone unless --force, so a real screenshot is never
overwritten. Fonts come from assets/fonts/ (override with OG_FONT_DIR); run
./font.sh first.
"""
import argparse
import os
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Brand palette - identical to generate_og.py
BG = (10, 10, 15)         # --bg        #0a0a0f
GOLD = (210, 188, 147)    # --accent    #d2bc93
TEXT = (232, 232, 240)    # --text      #e8e8f0
DIM = (154, 154, 176)     # --text-dim  #9a9ab0
GRID = (20, 20, 28)
PILL_BG = (26, 26, 38)    # --bg-3      #1a1a26
PILL_EDGE = (37, 37, 58)  # --border    #25253a

W, H = 1200, 900          # 4:3, matches .project-image aspect-ratio
MARGIN = 72

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
FONT_DIR = Path(os.environ.get("OG_FONT_DIR", REPO / "assets" / "fonts"))

ARTICLE = re.compile(r'<article class="project">.*?</article>', re.DOTALL)
IMG_SRC = re.compile(r'<img\s+src="assets/([a-zA-Z0-9._/-]+)\.png"')
GH_LINK = re.compile(r'github\.com/RNVizion/([a-zA-Z0-9._-]+)')


# --------------------------------------------------------------------------
# parsing and validation
# --------------------------------------------------------------------------


# Mark tracking: 1.8px absolute, ruled for all raster surfaces in
# BRAND_TYPE.md rev 3 (2026-08-15). Absolute rather than em because an em value
# exists so tracking scales with type size, and a raster mark has no type size
# to scale with -- the generator fixes it and the image renders at that size
# forever. Expressed as 0.09em at 20px and 0.06em at 30px, which is how each
# generator happens to reach the same optical gap, not the reason for it.
MARK_TRACK = 1.8


def draw_tracked(d, xy, text, font, fill, gap=MARK_TRACK):
    """Draw text with an absolute per-gap tracking value; return drawn width.

    PIL has no letter-spacing, so each glyph is placed and advanced by hand.
    This loses kerning pairs: measured on Montserrat Black, the advance sum runs
    0.20px wide of the kerned single-call width at 20px and 0.30px at 30px.
    Under a third of a pixel, recorded so it is not mistaken for a defect.
    """
    x, y = xy
    last = len(text) - 1
    for i, ch in enumerate(text):
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font)
        if i < last:
            x += gap
    return x - xy[0]


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def scan_projects(index_path):
    """Parse every project article into a record, with the slug cross-check applied."""
    if not index_path.exists():
        return []
    html = index_path.read_text(encoding="utf-8")
    out = []
    for block in ARTICLE.finditer(html):
        b = block.group(0)
        img = IMG_SRC.search(b)
        if not img:
            continue
        path = img.group(1)          # "rnv-color-mcp" or "brand/aiii-og"
        title = re.search(r"<h3>(.*?)</h3>", b, re.DOTALL)
        label = re.search(r'<div class="project-number">(.*?)</div>', b, re.DOTALL)
        repos = GH_LINK.findall(b)

        rec = {
            "path": path,
            "title": strip_tags(title.group(1)) if title else "",
            "label": strip_tags(label.group(1)) if label else "",
            "tags": [strip_tags(t) for t in
                     re.findall(r'<span class="tag">(.*?)</span>', b, re.DOTALL)],
            "repo": repos[0] if repos else None,
            "exists": (REPO / "assets" / f"{path}.png").exists(),
        }

        if "/" in path:
            rec["status"] = "exempt"        # assets/brand/... is not a project card
        elif rec["repo"] is None:
            rec["status"] = "unverified"    # nothing to cross-check against
        elif rec["repo"] != path:
            rec["status"] = "mismatch"      # the typo case
        else:
            rec["status"] = "ok"
        out.append(rec)
    return out


def report(records):
    """Print the scan table. Returns the number of mismatches."""
    print(f"{'status':<12} {'image':<36} repo")
    print("-" * 80)
    mismatches = 0
    for r in records:
        left = f"assets/{r['path']}.png"
        if r["status"] == "mismatch":
            mismatches += 1
            print(f"{'MISMATCH':<12} {left:<36} github.com/RNVizion/{r['repo']}")
            print(f"{'':<12} ^ expected assets/{r['repo']}.png - likely a typo")
        elif r["status"] == "exempt":
            print(f"{'exempt':<12} {left:<36} (not a project card)")
        elif r["status"] == "unverified":
            print(f"{'unverified':<12} {left:<36} (no GitHub link to check against)")
        else:
            print(f"{('ok' if r['exists'] else 'missing'):<12} {left:<36} "
                  f"github.com/RNVizion/{r['repo']}")
    return mismatches


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------
def load_font(path, size, weights=("SemiBold", "Bold", "Medium")):
    try:
        font = ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()
    for name in weights:
        try:
            font.set_variation_by_name(name)
            break
        except Exception:
            continue
    return font


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(title, label, tags, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=GRID, width=1)

    mark = load_font(FONT_DIR / "Montserrat.ttf", 30, weights=("Black",))
    dot_r = 7
    cy = MARGIN + 15
    d.ellipse([MARGIN, cy - dot_r, MARGIN + 2 * dot_r, cy + dot_r], fill=GOLD)
    draw_tracked(d, (MARGIN + 2 * dot_r + 14, MARGIN), "RNVizion", mark, TEXT)

    label_font = load_font(FONT_DIR / "JetBrainsMono.ttf", 26, weights=("Medium", "Bold"))
    tag_font = load_font(FONT_DIR / "JetBrainsMono.ttf", 22, weights=("Medium", "Bold"))

    pill_h, pad_x, gap = 44, 18, 12
    shown, row_w = [], 0
    max_row = W - 2 * MARGIN
    for t in tags[:5]:
        w = int(d.textlength(t, font=tag_font)) + 2 * pad_x
        if row_w + w + (gap if shown else 0) > max_row:
            break
        shown.append((t, w))
        row_w += w + (gap if len(shown) > 1 else 0)
    tags_h = pill_h + 34 if shown else 0

    title_x = MARGIN + 30
    max_w = W - title_x - MARGIN
    avail = H - 300 - tags_h
    size = 96
    while size >= 44:
        f = load_font(FONT_DIR / "BricolageGrotesque.ttf", size)
        if len(wrap(d, title, f, max_w)) <= 4 and \
           int(size * 1.14) * len(wrap(d, title, f, max_w)) <= avail:
            break
        size -= 4
    font = load_font(FONT_DIR / "BricolageGrotesque.ttf", size)
    lines = wrap(d, title, font, max_w)
    line_h = int(size * 1.14)
    block_h = line_h * len(lines)

    total = (44 if label else 0) + block_h + tags_h
    y = (H - total) // 2 + 10

    if label:
        d.text((title_x, y), label, font=label_font, fill=GOLD)
        y += 44

    d.rectangle([MARGIN, y + 6, MARGIN + 6, y + block_h - 10], fill=GOLD)
    for ln in lines:
        d.text((title_x, y), ln, font=font, fill=TEXT)
        y += line_h

    if shown:
        y += 22
        x = MARGIN
        for t, w in shown:
            d.rounded_rectangle([x, y, x + w, y + pill_h], radius=6,
                                fill=PILL_BG, outline=PILL_EDGE, width=1)
            tw = d.textlength(t, font=tag_font)
            d.text((x + (w - tw) / 2, y + 9), t, font=tag_font, fill=DIM)
            x += w + gap

    small = load_font(FONT_DIR / "JetBrainsMono.ttf", 26, weights=("Medium", "Bold"))
    domain = "rnvizion.dev"
    dw = d.textlength(domain, font=small)
    d.text((W - MARGIN - dw, H - MARGIN - 10), domain, font=small, fill=DIM)

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Render a brand card for a headless project.")
    ap.add_argument("slug", nargs="?", help="asset slug, e.g. rnv-publishing-agent")
    ap.add_argument("--check", action="store_true",
                    help="validate every project's image slug against its repo; render nothing")
    ap.add_argument("--all-missing", action="store_true",
                    help="validate, then render a card for each validated project missing one")
    ap.add_argument("--title", help="override the title from index.html")
    ap.add_argument("--label", help='override the category label, e.g. "04 / AGENTS"')
    ap.add_argument("--tags", help="override tags, comma separated")
    ap.add_argument("-o", "--output", help="output path (default assets/<slug>.png)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing image")
    ap.add_argument("--index", default=str(REPO / "index.html"),
                    help="page to read values from")
    args = ap.parse_args()

    index_path = Path(args.index)

    # ---- validate only ----
    if args.check:
        records = scan_projects(index_path)
        if not records:
            print(f"No project articles found in {index_path}.")
            return 1
        bad = report(records)
        print()
        if bad:
            print(f"{bad} slug mismatch(es). Fix the filename or the link so they agree.")
            return 1
        print("All project image slugs match their repo names.")
        return 0

    # ---- batch fill ----
    if args.all_missing:
        records = scan_projects(index_path)
        if [r for r in records if r["status"] == "mismatch"]:
            n = report(records)
            print()
            print(f"Refusing to generate: {n} image slug(s) do not match their repo.")
            print("A generated card would hide the typo behind a tile that looks correct.")
            return 1

        for r in records:
            if r["status"] == "unverified":
                print(f"note   assets/{r['path']}.png has no GitHub link to verify against",
                      file=sys.stderr)

        todo = [r for r in records
                if r["status"] in ("ok", "unverified") and not r["exists"]]
        if not todo:
            print("No missing project cards. Nothing to do.")
            return 0
        for r in todo:
            out = REPO / "assets" / f"{r['path']}.png"
            render(r["title"] or r["path"], r["label"], r["tags"], out)
            print(f"wrote  {out}  ({r['title']}"
                  f"{' - ' + r['label'] if r['label'] else ''})")
        return 0

    # ---- single slug ----
    if not args.slug:
        ap.error("give a slug, or use --all-missing / --check")

    out = Path(args.output) if args.output else REPO / "assets" / f"{args.slug}.png"
    if out.exists() and not args.force:
        print(f"skip   {out}  (exists; --force to replace)")
        return 0

    rec = next((r for r in scan_projects(index_path) if r["path"] == args.slug), None)
    if rec and rec["status"] == "mismatch" and not args.title:
        print(f"ERROR  assets/{args.slug}.png sits in the article linking to "
              f"github.com/RNVizion/{rec['repo']}", file=sys.stderr)
        print(f"       Expected assets/{rec['repo']}.png. Fix the filename or the link, "
              f"or pass --title to override.", file=sys.stderr)
        return 1

    title = args.title or (rec or {}).get("title") or args.slug.replace("-", " ").title()
    label = args.label if args.label is not None else (rec or {}).get("label", "")
    tags = ([t.strip() for t in args.tags.split(",") if t.strip()]
            if args.tags is not None else (rec or {}).get("tags", []))

    if not rec and not args.title:
        print(f"note   nothing in {index_path.name} references assets/{args.slug}.png; "
              f"using defaults", file=sys.stderr)

    render(title, label, tags, out)
    print(f"wrote  {out}  ({title}{' - ' + label if label else ''})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
