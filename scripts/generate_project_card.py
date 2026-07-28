#!/usr/bin/env python3
"""
generate_project_card.py — render a card image for a project that has no UI to
screenshot (an MCP server, an agent loop, a library).

Companion to generate_og.py: same brand palette, same faces, same wordmark, but
sized 4:3 to match the .project-image container on the homepage rather than the
1200x630 of an Open Graph share image.

SOURCE OF TRUTH
By default it reads index.html and finds the <article class="project"> whose
<img src> points at the card being generated, then pulls every value from that
markup, the same way generate_card.py pulls from a post:
  label <- <div class="project-number">   e.g. "04 / AGENTS"
  title <- <h3>                           e.g. "RNV Publishing Agent"
  tags  <- <span class="tag">             up to five, rendered as pills
Nothing is hand-copied, so the card can never drift from the page.

USAGE (run from the repo root)
  python scripts/generate_project_card.py rnv-publishing-agent
  python scripts/generate_project_card.py --all-missing
  python scripts/generate_project_card.py rnv-color-mcp --force

  # standalone, no index.html lookup:
  python scripts/generate_project_card.py my-thing \\
      --title "RNV Something" --label "10 / TOOLS" --tags "Python,CLI" 

Existing files are left alone unless --force is passed, so this will never
overwrite a real screenshot.

Fonts come from assets/fonts/ (override with OG_FONT_DIR); run ./font.sh first.
"""
import argparse
import os
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Brand palette — identical to generate_og.py
BG = (10, 10, 15)        # --bg        #0a0a0f
GOLD = (210, 188, 147)   # --accent    #d2bc93
TEXT = (232, 232, 240)   # --text      #e8e8f0
DIM = (154, 154, 176)    # --text-dim  #9a9ab0
GRID = (20, 20, 28)
PILL_BG = (26, 26, 38)   # --bg-3      #1a1a26
PILL_EDGE = (37, 37, 58) # --border    #25253a

W, H = 1200, 900         # 4:3, matches .project-image aspect-ratio
MARGIN = 72

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
FONT_DIR = Path(os.environ.get("OG_FONT_DIR", REPO / "assets" / "fonts"))


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


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def from_index(slug, index_path):
    """Find the project article whose image is assets/<slug>.png; pull its values."""
    if not index_path.exists():
        return {}
    html = index_path.read_text(encoding="utf-8")
    for block in re.findall(r'<article class="project">.*?</article>', html, re.DOTALL):
        if f'assets/{slug}.png' not in block:
            continue
        label = re.search(r'<div class="project-number">(.*?)</div>', block, re.DOTALL)
        title = re.search(r"<h3>(.*?)</h3>", block, re.DOTALL)
        tags = re.findall(r'<span class="tag">(.*?)</span>', block, re.DOTALL)
        return {
            "label": strip_tags(label.group(1)) if label else "",
            "title": strip_tags(title.group(1)) if title else "",
            "tags": [strip_tags(t) for t in tags],
        }
    return {}


def render(title, label, tags, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # faint 48px grid, same texture as the OG cards
    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=GRID, width=1)

    # wordmark, top-left: gold dot + RNVizion
    mono = load_font(FONT_DIR / "JetBrainsMono.ttf", 30, weights=("Medium", "Bold"))
    dot_r = 7
    cy = MARGIN + 15
    d.ellipse([MARGIN, cy - dot_r, MARGIN + 2 * dot_r, cy + dot_r], fill=GOLD)
    d.text((MARGIN + 2 * dot_r + 14, MARGIN), "RNVizion", font=mono, fill=TEXT)

    # category label, gold mono, above the title
    label_font = load_font(FONT_DIR / "JetBrainsMono.ttf", 26, weights=("Medium", "Bold"))

    # tags first: we need their height to centre the block properly
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

    # title, auto-sized to fit the space left over
    title_x = MARGIN + 30
    max_w = W - title_x - MARGIN
    avail = H - 300 - tags_h
    size = 96
    while size >= 44:
        f = load_font(FONT_DIR / "BricolageGrotesque.ttf", size)
        lines = wrap(d, title, f, max_w)
        if len(lines) <= 4 and int(size * 1.14) * len(lines) <= avail:
            break
        size -= 4
    font = load_font(FONT_DIR / "BricolageGrotesque.ttf", size)
    lines = wrap(d, title, font, max_w)
    line_h = int(size * 1.14)
    block_h = line_h * len(lines)

    total = (44 if label else 0) + block_h + tags_h
    y0 = (H - total) // 2 + 10

    y = y0
    if label:
        d.text((title_x, y), label, font=label_font, fill=GOLD)
        y += 44

    # gold accent bar beside the title, same device as the OG card
    d.rectangle([MARGIN, y + 6, MARGIN + 6, y + block_h - 10], fill=GOLD)
    for ln in lines:
        d.text((title_x, y), ln, font=font, fill=TEXT)
        y += line_h

    # tag pills
    if shown:
        y += 34 - 12
        x = MARGIN
        for t, w in shown:
            d.rounded_rectangle([x, y, x + w, y + pill_h], radius=6,
                                fill=PILL_BG, outline=PILL_EDGE, width=1)
            tw = d.textlength(t, font=tag_font)
            d.text((x + (w - tw) / 2, y + 9), t, font=tag_font, fill=DIM)
            x += w + gap

    # domain, bottom-right
    small = load_font(FONT_DIR / "JetBrainsMono.ttf", 26, weights=("Medium", "Bold"))
    domain = "rnvizion.dev"
    dw = d.textlength(domain, font=small)
    d.text((W - MARGIN - dw, H - MARGIN - 10), domain, font=small, fill=DIM)

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def missing_cards(index_path):
    """Every assets/*.png referenced by a project article that has no file yet."""
    if not index_path.exists():
        return []
    html = index_path.read_text(encoding="utf-8")
    out = []
    for block in re.findall(r'<article class="project">.*?</article>', html, re.DOTALL):
        m = re.search(r'src="assets/([a-zA-Z0-9._-]+)\.png"', block)
        if m and not (REPO / "assets" / f"{m.group(1)}.png").exists():
            out.append(m.group(1))
    return out


def main():
    ap = argparse.ArgumentParser(description="Render a brand card for a headless project.")
    ap.add_argument("slug", nargs="?", help="asset slug, e.g. rnv-publishing-agent")
    ap.add_argument("--all-missing", action="store_true",
                    help="render a card for every project image referenced but absent")
    ap.add_argument("--title", help="override the title from index.html")
    ap.add_argument("--label", help='override the category label, e.g. "04 / AGENTS"')
    ap.add_argument("--tags", help="override tags, comma separated")
    ap.add_argument("-o", "--output", help="output path (default assets/<slug>.png)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing image")
    ap.add_argument("--index", default=str(REPO / "index.html"), help="page to read values from")
    args = ap.parse_args()

    index_path = Path(args.index)

    if args.all_missing:
        slugs = missing_cards(index_path)
        if not slugs:
            print("No missing project cards. Nothing to do.")
            return 0
    elif args.slug:
        slugs = [args.slug]
    else:
        ap.error("give a slug, or use --all-missing")

    for slug in slugs:
        out = Path(args.output) if args.output else REPO / "assets" / f"{slug}.png"
        if out.exists() and not args.force:
            print(f"skip   {out}  (exists; --force to replace)")
            continue

        data = from_index(slug, index_path)
        title = args.title or data.get("title") or slug.replace("-", " ").title()
        label = args.label if args.label is not None else data.get("label", "")
        if args.tags is not None:
            tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        else:
            tags = data.get("tags", [])

        if not data and not args.title:
            print(f"note   no <article class=\"project\"> in {index_path.name} references "
                  f"assets/{slug}.png; using defaults", file=sys.stderr)

        render(title, label, tags, out)
        print(f"wrote  {out}  ({title}{' · ' + label if label else ''})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())