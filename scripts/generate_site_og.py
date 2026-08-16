#!/usr/bin/env python3
"""
generate_site_og.py — render assets/og-image.png, the site-wide Open Graph card.

This is the card LinkedIn, Slack, and X show for rnvizion.dev, /resume/, and
/bio/ (every page whose og:image points at assets/og-image.png). It used to be
made by hand, which is how it ended up claiming 5,003 tests while the homepage
said 5,021.

SOURCE OF TRUTH
Every value is read out of the page it represents, the same discipline
generate_og.py and generate_project_card.py already follow. Two page shapes:

  homepage (index.html)
    name     <- <h1>, up to the colon
    tagline  <- <h1> after the colon, else .hero-subtitle
    footer   <- .about-stats tiles, rendered as value + label

  résumé (resume/index.html) and any page like it
    kicker   <- og:title, the part before the em dash ("Résumé")
    name     <- <h1>
    tagline  <- .tagline
    footer   <- <meta name="card:anchors">, a separator-delimited list

card:anchors reuses the card: meta namespace already used for card:summary on
blog posts. Putting the anchors in the page rather than in this script keeps
the no-drift property: edit the page, the card follows.

USAGE (run from the repo root)
  python scripts/generate_site_og.py            # site-wide card from index.html
  python scripts/generate_site_og.py --page resume/index.html -o assets/og-resume.png
  python scripts/generate_site_og.py --all      # every card configured in PAGES
  python scripts/generate_site_og.py --check    # compare cards vs pages, render nothing

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

# Every card this script owns: source page -> output file.
PAGES = [
    ("index.html", "assets/og-image.png"),
    ("resume/index.html", "assets/og-resume.png"),
]


# --------------------------------------------------------------------------
# reading the page
# --------------------------------------------------------------------------
# Long stat labels from the page ("Projects Shipped") read as clutter at card
# size, where the original card used one word. Take the first word, and give
# the few that are still long a conventional short form.
LABEL_SHORT = {"CERTIFICATIONS": "CERTS", "CERTIFICATES": "CERTS"}


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


def short_label(label):
    first = label.split()[0] if label.split() else label
    return LABEL_SHORT.get(first, first)


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def read_page(page_path):
    """Pull kicker, name, tagline, and footer items out of a page.

    Shape-aware: a page carrying .about-stats gets a stats footer; a page
    carrying <meta name="card:anchors"> gets an anchors footer.
    """
    html = page_path.read_text(encoding="utf-8")

    h1 = re.search(r"<h1>(.*?)</h1>", html, re.DOTALL)
    name = strip_tags(h1.group(1)) if h1 else "Christian Smith"
    tagline = ""
    if ":" in name:
        name, _, remainder = name.partition(":")
        name, tagline = name.strip(), remainder.strip()

    # kicker: og:title up to the em dash, when it names something else
    # A kicker only exists when og:title is "<Label> \u2014 <Name>": the em dash
    # is what marks the label. Without it (the homepage reads "Christian Smith,
    # AI Engineer & Developer") there is no kicker, and the whole title must not
    # be mistaken for one.
    kicker = ""
    og = re.search(r'og:title"\s+content="(.*?)"', html)
    if og and "\u2014" in og.group(1):
        head = og.group(1).split("\u2014")[0].strip()
        if head and len(head) <= 20 and head.lower() not in name.lower():
            kicker = head.upper()

    if not tagline:
        for pattern in (r'hero-subtitle">(.*?)</p>', r'class="tagline">(.*?)</p>'):
            m = re.search(pattern, html, re.DOTALL)
            if m:
                tagline = strip_tags(m.group(1)).split(":")[0].strip()
                break

    stats, anchors = [], []
    for value, label in re.findall(
        r'stat-value">(.*?)</div>\s*<div class="stat-label">(.*?)</div>', html, re.DOTALL
    ):
        v, l = strip_tags(value), strip_tags(label).upper()
        if re.search(r"\d", v):
            stats.append((v, short_label(l)))

    if not stats:
        m = re.search(r'name="card:anchors"\s+content="(.*?)"', html)
        if m:
            anchors = [a.strip() for a in re.split(r"[\u00b7|]", m.group(1)) if a.strip()]

    return {"kicker": kicker, "name": name, "tagline": tagline,
            "stats": stats[:3], "anchors": anchors[:4]}


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

    # wordmark: gold dot + RNVizion (Montserrat Black, Brand Book #15).
    # Case AND tracking match the web surfaces as of BRAND_TYPE.md rev 3: 1.8px
    # absolute, which at this 20px mark is the 0.09em the nav carries.
    #
    # The comment replaced here claimed the ruled value was +0.033em and that it
    # was sub-pixel at 20px, so no tracking was applied. The ruled value was
    # 0.09em; +0.033em had already been superseded. The conclusion outlived its
    # reasoning because the reasoning read confident and cited a real number --
    # what found it was checking the value the comment NAMED against the value
    # actually ruled, not re-deriving the conclusion.
    mark_f = load_font(FONT_DIR / "Montserrat.ttf", 20, weights=("Black",))
    dot_r = 6
    cy = MARGIN + 10
    d.ellipse([MARGIN, cy - dot_r, MARGIN + 2 * dot_r, cy + dot_r], fill=GOLD)
    draw_tracked(d, (MARGIN + 2 * dot_r + 12, MARGIN), "RNVizion", mark_f, GOLD)

    # optional kicker (e.g. "RÉSUMÉ") above the name
    name_y = MARGIN + 78
    if data.get("kicker"):
        kick = load_font(FONT_DIR / "JetBrainsMono.ttf", 22, weights=("Medium", "Bold"))
        d.text((MARGIN, name_y - 6), " ".join(data["kicker"]), font=kick, fill=DIM)
        name_y += 34

    # name
    name_font = load_font(FONT_DIR / "BricolageGrotesque.ttf", 88)
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

    # anchors footer: gold-dotted phrases, right-aligned (résumé-shaped pages)
    if data.get("anchors") and not data["stats"]:
        af = load_font(FONT_DIR / "JetBrainsMono.ttf", 24, weights=("Medium", "Bold"))
        gap, dot_gap, r = 34, 14, 4
        widths = [d.textlength(a, font=af) for a in data["anchors"]]
        total = sum(widths) + sum(2 * r + dot_gap for _ in widths) + gap * (len(widths) - 1)
        x = W - MARGIN - total
        cy = H - MARGIN - 34
        for a, w in zip(data["anchors"], widths):
            d.ellipse([x, cy - r, x + 2 * r, cy + r], fill=GOLD)
            x += 2 * r + dot_gap
            d.text((x, cy - 15), a, font=af, fill=DIM)
            x += w + gap
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out, "PNG")
        return out

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
    ap.add_argument("--page", "--index", dest="page", default=str(REPO / "index.html"),
                    help="source page to read (default index.html)")
    ap.add_argument("--all", action="store_true",
                    help="render every card in PAGES")
    ap.add_argument("-o", "--output", default=str(DEFAULT_OUT))
    ap.add_argument("--tagline", help="override the tagline read from the page")
    ap.add_argument("--role", default="Python developer · AR/VR at Meta",
                    help="the role line under the name")
    ap.add_argument("--stats", help='override stat tiles, e.g. "9:PROJECTS,5021:TESTS,10:CERTS"')
    args = ap.parse_args()

    if args.all:
        rc = 0
        for src, dst in PAGES:
            sp, op = REPO / src, REPO / dst
            if not sp.exists():
                print(f"skip   {src} not found"); rc = 1; continue
            data = read_page(sp)
            if args.check:
                stale = not op.exists() or op.stat().st_mtime < sp.stat().st_mtime
                print(f"{'STALE ' if stale else 'ok    '} {dst}  <- {src}")
                rc = rc or int(stale)
            else:
                render(data, op, role_line=args.role)
                print(f"wrote  {dst}  <- {src}")
        return rc

    index_path = Path(args.page)
    if not index_path.exists():
        print(f"error: {index_path} not found. Run from the repo root.", file=sys.stderr)
        return 2

    data = read_page(index_path)
    if args.tagline:
        data["tagline"] = args.tagline
    if args.stats:
        data["stats"] = [tuple(p.split(":", 1)) for p in args.stats.split(",") if ":" in p]

    out = Path(args.output)

    print(f"from {index_path}:")
    if data.get("kicker"):
        print(f"  kicker  {data['kicker']}")
    print(f"  name    {data['name']}")
    print(f"  tagline {data['tagline']}")
    if data["stats"]:
        print(f"  stats   {' · '.join(f'{v} {l}' for v, l in data['stats'])}")
    if data["anchors"]:
        print(f"  anchors {' · '.join(data['anchors'])}")
    if not data["stats"] and not data["anchors"]:
        print("  footer  (none: no .about-stats and no card:anchors meta)")

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
