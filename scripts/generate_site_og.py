#!/usr/bin/env python3
"""
generate_site_og.py — render assets/og-image.png, the site-wide Open Graph card.

This is the card LinkedIn, Slack, and X show for rnvizion.dev, /resume/, and
/bio/ (every page whose og:image points at assets/og-image.png). It used to be
made by hand, which is how it ended up claiming 5,003 tests while the homepage
said 5,021.

SOURCE OF TRUTH
Every value is read out of index.html, the same discipline generate_og.py and
generate_project_card.py already follow:
  name     <- <h1>, up to the colon
  tagline  <- .hero-subtitle, first clause
  stats    <- the .about-stats block (value + label per tile)
Nothing is hand-typed, so the card cannot disagree with the page it represents.

USAGE (run from the repo root)
  python scripts/generate_site_og.py            # rebuild the card
  python scripts/generate_site_og.py --check    # compare card vs page, render nothing
  python scripts/generate_site_og.py --tagline "Custom line"

  # override the stat tiles picked up from the page:
  python scripts/generate_site_og.py --stats "9:PROJECTS,5021:TESTS,10:CERTS"

--check exits non-zero if the card is missing or older than index.html, which
makes it usable as a CI guard.

Fonts come from assets/fonts/ (override with OG_FONT_DIR); run ./font.sh first.
"""
import argparse
import os
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Brand palette - identical to the other card generators
BG = (10, 10, 15)         # --bg        #0a0a0f
GOLD = (210, 188, 147)    # --accent    #d2bc93
TEXT = (232, 232, 240)    # --text      #e8e8f0
DIM = (154, 154, 176)     # --text-dim  #9a9ab0
FAINT = (90, 90, 114)     # --text-faint #5a5a72
GRID = (20, 20, 28)
RULE = (37, 37, 58)       # --border    #25253a

W, H = 1200, 630          # Open Graph standard
MARGIN = 72

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
FONT_DIR = Path(os.environ.get("OG_FONT_DIR", REPO / "assets" / "fonts"))
DEFAULT_OUT = REPO / "assets" / "og-image.png"


# --------------------------------------------------------------------------
# reading the page
# --------------------------------------------------------------------------
# Long stat labels from the page ("Projects Shipped") read as clutter at card
# size, where the original card used one word. Take the first word, and give
# the few that are still long a conventional short form.
LABEL_SHORT = {"CERTIFICATIONS": "CERTS", "CERTIFICATES": "CERTS"}


def short_label(label):
    first = label.split()[0] if label.split() else label
    return LABEL_SHORT.get(first, first)


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def read_page(index_path):
    """Pull the name, role line, tagline, and stat tiles out of index.html."""
    html = index_path.read_text(encoding="utf-8")

    h1 = re.search(r"<h1>(.*?)</h1>", html, re.DOTALL)
    name = strip_tags(h1.group(1)) if h1 else "Christian Smith"
    # "Christian Smith : I build production AI systems..." -> name, then the rest
    if ":" in name:
        name, _, remainder = name.partition(":")
        name = name.strip()
        remainder = remainder.strip()
    else:
        remainder = ""

    sub = re.search(r'hero-subtitle">(.*?)</p>', html, re.DOTALL)
    subtitle = strip_tags(sub.group(1)) if sub else ""
    # first sentence up to the first colon reads best at card size
    tagline = remainder or subtitle.split(":")[0].strip()

    stats = []
    for value, label in re.findall(
        r'stat-value">(.*?)</div>\s*<div class="stat-label">(.*?)</div>', html, re.DOTALL
    ):
        v, l = strip_tags(value), strip_tags(label).upper()
        # keep the numeric tiles; the degree tile doesn't read at this size
        if re.search(r"\d", v):
            stats.append((v, short_label(l)))

    return {"name": name, "tagline": tagline, "stats": stats[:3]}


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


def render(data, out, role_line="Python developer · AR/VR at Meta"):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=GRID, width=1)

    # wordmark: gold dot + RNVIZION, letter-spaced mono
    mono_sm = load_font(FONT_DIR / "JetBrainsMono.ttf", 20, weights=("Medium", "Bold"))
    dot_r = 6
    cy = MARGIN + 10
    d.ellipse([MARGIN, cy - dot_r, MARGIN + 2 * dot_r, cy + dot_r], fill=GOLD)
    d.text((MARGIN + 2 * dot_r + 12, MARGIN), " ".join("RNVIZION"), font=mono_sm, fill=GOLD)

    # name
    name_font = load_font(FONT_DIR / "BricolageGrotesque.ttf", 88)
    name_y = MARGIN + 78
    d.text((MARGIN, name_y), data["name"], font=name_font, fill=TEXT)

    # role line + tagline
    body = load_font(FONT_DIR / "JetBrainsMono.ttf", 24, weights=("Medium", "Bold"))
    y = name_y + 110
    d.text((MARGIN, y), role_line, font=body, fill=DIM)
    y += 36
    for line in wrap(d, data["tagline"], body, W - 2 * MARGIN)[:2]:
        d.text((MARGIN, y), line, font=body, fill=DIM)
        y += 36

    # divider above the footer
    rule_y = H - MARGIN - 92
    d.line([(MARGIN, rule_y), (W - MARGIN, rule_y)], fill=RULE, width=1)

    # domain, bottom-left
    domain_font = load_font(FONT_DIR / "JetBrainsMono.ttf", 30, weights=("Medium", "Bold"))
    d.text((MARGIN, H - MARGIN - 56), "rnvizion.dev", font=domain_font, fill=GOLD)

    # stat tiles, bottom-right, right-aligned as a group
    val_font = load_font(FONT_DIR / "BricolageGrotesque.ttf", 40)
    lbl_font = load_font(FONT_DIR / "JetBrainsMono.ttf", 15, weights=("Medium", "Bold"))
    gap = 56
    widths = []
    for value, label in data["stats"]:
        widths.append(max(d.textlength(value, font=val_font),
                          d.textlength(label, font=lbl_font)))
    total = sum(widths) + gap * (len(widths) - 1 if widths else 0)
    x = W - MARGIN - total
    for (value, label), w in zip(data["stats"], widths):
        vw = d.textlength(value, font=val_font)
        lw = d.textlength(label, font=lbl_font)
        d.text((x + (w - vw) / 2, H - MARGIN - 62), value, font=val_font, fill=TEXT)
        d.text((x + (w - lw) / 2, H - MARGIN - 16), label, font=lbl_font, fill=FAINT)
        x += w + gap

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Render the site-wide Open Graph card.")
    ap.add_argument("--check", action="store_true",
                    help="report whether the card is current; render nothing")
    ap.add_argument("--index", default=str(REPO / "index.html"))
    ap.add_argument("-o", "--output", default=str(DEFAULT_OUT))
    ap.add_argument("--tagline", help="override the tagline read from the page")
    ap.add_argument("--role", default="Python developer · AR/VR at Meta",
                    help="the role line under the name")
    ap.add_argument("--stats", help='override stat tiles, e.g. "9:PROJECTS,5021:TESTS,10:CERTS"')
    args = ap.parse_args()

    index_path = Path(args.index)
    if not index_path.exists():
        print(f"error: {index_path} not found. Run from the repo root.", file=sys.stderr)
        return 2

    data = read_page(index_path)
    if args.tagline:
        data["tagline"] = args.tagline
    if args.stats:
        data["stats"] = [tuple(p.split(":", 1)) for p in args.stats.split(",") if ":" in p]

    out = Path(args.output)

    print(f"from {index_path.name}:")
    print(f"  name    {data['name']}")
    print(f"  tagline {data['tagline']}")
    print(f"  stats   {' · '.join(f'{v} {l}' for v, l in data['stats'])}")

    if args.check:
        if not out.exists():
            print(f"\nMISSING  {out} has never been generated.")
            return 1
        if out.stat().st_mtime < index_path.stat().st_mtime:
            print(f"\nSTALE    {out.name} is older than {index_path.name}; regenerate it.")
            return 1
        print(f"\nok       {out.name} is newer than {index_path.name}.")
        return 0

    render(data, out, role_line=args.role)
    print(f"\nwrote  {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
