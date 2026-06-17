#!/usr/bin/env python3
"""
generate_card.py — build a blog-index post card from a published post.

Reads a post's index.html (the one produced from post-template.html), pulls
every value the card needs straight from the post's own tags, fills the card
template, and prints the result. One source of truth per value, no hand-copying.

WHAT IT PULLS FROM THE POST
  title    <- og:title            (falls back to <title>, minus " — Christian Smith")
  slug     <- og:url              (the <slug> in /blog/<slug>/)
  date     <- article:published_time   (YYYY-MM-DD -> "Month Day, Year")
  read     <- computed from the <article> word count (~200 wpm, override --wpm)
  summary  <- priority order:
                1. --summary "..."                         (CLI override)
                2. <meta name="card:summary" content="..."> (teaser, if present)
                3. og:description                          (SEO line, fallback)

USAGE (run from the repo root)
  python scripts/generate_card.py blog/squish/index.html
  python scripts/generate_card.py blog/squish/index.html --summary "Your teaser here."
  python scripts/generate_card.py blog/squish/index.html -o card.html
  python scripts/generate_card.py blog/squish/index.html --template path/to/post-card-template.html

The card template is found automatically: next to this script, in the repo's
_templates/ folder, or in the current directory. Pass --template to override.
Output goes to stdout unless -o is given.
"""

import argparse
import os
import re
import sys
from datetime import datetime


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def strip_comments(html):
    return re.sub(r"<!--.*?-->", "", html, flags=re.S)


def meta(html, attr, value):
    """Grab a <meta {attr}="{value}" content="..."> field. Returns '' if absent.

    Uses a backreference on the content delimiter so a straight quote or
    apostrophe inside the value (e.g. "Can't") doesn't end the match early.
    """
    m = re.search(
        rf'<meta\s+{attr}=["\']{re.escape(value)}["\']\s+content=(["\'])(.*?)\1',
        html,
        flags=re.I | re.S,
    )
    return m.group(2).strip() if m else ""


def extract_title(html):
    title = meta(html, "property", "og:title")
    if title:
        return title
    m = re.search(r"<title>(.*?)</title>", html, flags=re.S)
    if not m:
        return ""
    # Drop the trailing site/author suffix the post template adds.
    return re.sub(r"\s*[—-]\s*Christian Smith\s*$", "", m.group(1)).strip()


def extract_slug(html):
    url = meta(html, "property", "og:url")
    m = re.search(r"/blog/([^/]+)/?", url)
    return m.group(1) if m else ""


def pretty_date(html):
    raw = meta(html, "property", "article:published_time")
    if not raw:
        return ""
    # Accept a plain YYYY-MM-DD or a full ISO timestamp.
    raw = raw.split("T")[0]
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return raw  # leave whatever was there if it doesn't parse
    return f"{dt:%B} {dt.day}, {dt.year}"  # no leading zero on the day


def read_minutes(html, wpm):
    """Word count of the real <article> body, comments and bio excluded."""
    body = strip_comments(html)
    m = re.search(r"<article[^>]*>(.*?)</article>", body, flags=re.S)
    if not m:
        return 1
    art = m.group(1)
    art = re.sub(r'<div class="bio">.*?</div>', "", art, flags=re.S)
    words = re.sub(r"<[^>]+>", " ", art).split()
    return max(1, round(len(words) / wpm))


def pick_summary(html, cli_summary):
    if cli_summary:
        return cli_summary.strip()
    card = meta(html, "name", "card:summary")
    if card:
        return card
    return meta(html, "property", "og:description")


def find_template(explicit):
    if explicit:
        return explicit
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)  # if this script lives in scripts/, this is the repo root
    cwd = os.getcwd()
    # Checked in order: next to the script, the repo's _templates/, then the cwd.
    candidates = (
        os.path.join(here, "post-card-template.html"),
        os.path.join(here, "_templates", "post-card-template.html"),
        os.path.join(repo_root, "_templates", "post-card-template.html"),
        os.path.join(cwd, "post-card-template.html"),
        os.path.join(cwd, "_templates", "post-card-template.html"),
    )
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    sys.exit(
        "error: could not find post-card-template.html in scripts/ or _templates/ "
        "(pass one explicitly with --template)"
    )


def fill_card(template_html, *, slug, date, minutes, title, summary):
    card = strip_comments(template_html).strip()
    replacements = {
        "[POST-SLUG]": slug,
        "[Month Day, Year]": date,
        "[X]": str(minutes),
        "[POST TITLE]": title,
        "[ONE-LINE CARD SUMMARY.]": summary,
        "[ONE-LINE CARD SUMMARY]": summary,  # tolerate the period-less form
    }
    for token, value in replacements.items():
        card = card.replace(token, value)

    leftover = re.findall(r"\[[A-Z][^\]]*\]", card)
    if leftover:
        sys.stderr.write(
            "warning: unfilled placeholders remain: " + ", ".join(leftover) + "\n"
        )
    return card


def main():
    p = argparse.ArgumentParser(description="Build a blog-index card from a post.")
    p.add_argument("post", help="path to the post's index.html")
    p.add_argument("--template", help="path to post-card-template.html")
    p.add_argument("--summary", help="override the card teaser line")
    p.add_argument("--wpm", type=int, default=200, help="words-per-minute (default 200)")
    p.add_argument("-o", "--output", help="write to a file instead of stdout")
    args = p.parse_args()

    post_html = read(args.post)
    template_html = read(find_template(args.template))

    title = extract_title(post_html)
    slug = extract_slug(post_html)
    date = pretty_date(post_html)
    minutes = read_minutes(post_html, args.wpm)
    summary = pick_summary(post_html, args.summary)

    for label, value in (("title", title), ("slug", slug), ("date", date), ("summary", summary)):
        if not value:
            sys.stderr.write(f"warning: could not derive {label} from the post\n")

    card = fill_card(
        template_html,
        slug=slug,
        date=date,
        minutes=minutes,
        title=title,
        summary=summary,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(card + "\n")
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        print(card)


if __name__ == "__main__":
    main()
