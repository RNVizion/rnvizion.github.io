#!/usr/bin/env python3
"""
generate_og.py — render a per-post Open Graph share image (1200x630) for a blog
post, in the RNVizion palette: near-black ground, gold accent, the post title in
the display face, and the RNVizion wordmark.

USAGE (run from the repo root)
  python scripts/generate_og.py blog/<slug>/index.html
  python scripts/generate_og.py blog/<slug>/index.html -o assets/og/<slug>.png

Fonts live in assets/fonts/ (override with OG_FONT_DIR). Drop these two there:
  BricolageGrotesque.ttf   (display)   JetBrainsMono.ttf  (wordmark)
If a font is missing the script still renders, just with a default face.
"""
import argparse
import os
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Brand palette (matches the site CSS variables)
BG = (10, 10, 15)        # --bg      #0a0a0f
GOLD = (210, 188, 147)   # --accent  #d2bc93
TEXT = (232, 232, 240)   # --text    #e8e8f0
DIM = (154, 154, 176)    # --text-dim #9a9ab0
GRID = (20, 20, 28)      # barely-there grid line

W, H = 1200, 630
MARGIN = 72

HERE = Path(__file__).resolve().parent
REPO = HERE.parent  # scripts/ -> repo root
FONT_DIR = Path(os.environ.get("OG_FONT_DIR", REPO / "assets" / "fonts"))


def load_font(path, size, weights=("SemiBold", "Bold", "Medium")):
    try:
        font = ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()
    for name in weights:  # variable fonts: pick a heavier instance if available
        try:
            font.set_variation_by_name(name)
            break
        except Exception:
            continue
    return font


def og_title(html):
    m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=(["\'])(.*?)\1', html, flags=re.I | re.S)
    if m:
        return m.group(2).strip()
    m = re.search(r"<title>(.*?)</title>", html, flags=re.S)
    return re.sub(r"\s*[—-]\s*Christian Smith\s*$", "", m.group(1)).strip() if m else "Untitled"


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


def render(title, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # faint 48px grid for brand texture
    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=GRID, width=1)

    # wordmark, top-left: gold dot + RNVizion (mono)
    mono = load_font(FONT_DIR / "JetBrainsMono.ttf", 30, weights=("Medium", "Bold"))
    dot_r = 7
    cy = MARGIN + 15
    d.ellipse([MARGIN, cy - dot_r, MARGIN + 2 * dot_r, cy + dot_r], fill=GOLD)
    d.text((MARGIN + 2 * dot_r + 14, MARGIN), "RNVizion", font=mono, fill=TEXT)

    # title, auto-sized to fit, with a gold accent bar to its left
    title_x = MARGIN + 30
    max_w = W - title_x - MARGIN
    size = 94
    while size >= 50:
        font = load_font(FONT_DIR / "BricolageGrotesque.ttf", size)
        lines = wrap(d, title, font, max_w)
        line_h = int(size * 1.14)
        if len(lines) <= 4 and line_h * len(lines) <= H - 320:
            break
        size -= 4
    font = load_font(FONT_DIR / "BricolageGrotesque.ttf", size)
    lines = wrap(d, title, font, max_w)
    line_h = int(size * 1.14)
    block_h = line_h * len(lines)
    y0 = (H - block_h) // 2 + 20

    d.rectangle([MARGIN, y0 + 6, MARGIN + 6, y0 + block_h - 10], fill=GOLD)
    y = y0
    for ln in lines:
        d.text((title_x, y), ln, font=font, fill=TEXT)
        y += line_h

    # domain, bottom-right (dim mono)
    small = load_font(FONT_DIR / "JetBrainsMono.ttf", 26, weights=("Medium", "Bold"))
    domain = "rnvizion.dev"
    dw = d.textlength(domain, font=small)
    d.text((W - MARGIN - dw, H - MARGIN - 10), domain, font=small, fill=DIM)

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def main():
    ap = argparse.ArgumentParser(description="Render a post's OG share image.")
    ap.add_argument("post", help="path to blog/<slug>/index.html")
    ap.add_argument("-o", "--output", help="output PNG (default assets/og/<slug>.png)")
    args = ap.parse_args()

    post = Path(args.post)
    if not post.exists():
        sys.exit(f"post not found: {post}")
    title = og_title(post.read_text(encoding="utf-8"))
    slug = post.parent.name
    out = args.output or (REPO / "assets" / "og" / f"{slug}.png")
    written = render(title, out)
    print(f"wrote {written}  (title: {title})")


if __name__ == "__main__":
    main()
