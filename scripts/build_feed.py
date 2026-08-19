#!/usr/bin/env python3
"""
build_feed.py — generate /feed.xml AND /blog/index.html for rnvizion.dev from the
blog post HTML files.

Each post lives at blog/<slug>/index.html and carries its metadata in the <head>.
The post body is whatever sits inside <article>.

The script reads every post once, sorts newest-first by published_time, then writes:
  - feed.xml at the repo root (served at https://rnvizion.dev/feed.xml)
  - the post-card list in blog/index.html, between the <!-- posts:start --> and
    <!-- posts:end --> markers (the surrounding page shell is left untouched)
  - sitemap.xml at the repo root, covering the blog posts AND the non-blog
    surfaces (/, /blog/, /aiii/, /bio/, /resume/, ...)
  - robots.txt at the repo root, pointing crawlers at the sitemap

A non-blog page is included in the sitemap only if it declares an og:url and is
not a redirect stub (no meta http-equiv=refresh). That rule keeps alias stubs
like /live/ — which forward elsewhere and canonicalise away — out of the sitemap
automatically, with no hardcoded exclude list to maintain.

The index cards are rendered by generate_card.py — the SAME renderer and template
the publishing agent uses — so a card here and a card the agent inserts are
byte-identical. There is one definition of a card (post-card-template.html); both
the agent and this script fill it. (generate_card.py must sit beside this file in
scripts/, which it does.)

Run from the repo root:  python scripts/build_feed.py
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape

from bs4 import BeautifulSoup

import generate_card as gc  # the shared card renderer (same folder)

# ----- Site constants: edit these for your channel-level metadata --------------
SITE_URL = "https://rnvizion.dev"
FEED_URL = f"{SITE_URL}/feed.xml"
SITE_TITLE = "RNVizion — Dev & Philosophy"
SITE_DESCRIPTION = (
    "Development and philosophy from Christian Smith (RNVizion): building software "
    "with a soul in a fast age."
)
SITE_LANGUAGE = "en-us"
BLOG_DIR = Path("blog")
OUTPUT = Path("feed.xml")
SITEMAP = Path("sitemap.xml")
ROBOTS = Path("robots.txt")
INDEX_FILE = BLOG_DIR / "index.html"
# Directories never scanned for sitemap pages (no public index.html of their own).
SKIP_DIRS = {"_templates", "scripts", "assets", ".github", ".git", "node_modules"}
POSTS_START = "<!-- posts:start -->"
POSTS_END = "<!-- posts:end -->"
# ------------------------------------------------------------------------------


def meta(soup: BeautifulSoup, *, prop: str | None = None, name: str | None = None) -> str | None:
    """Return the content of a <meta> tag matched by property= or name=."""
    if prop:
        tag = soup.find("meta", attrs={"property": prop})
    else:
        tag = soup.find("meta", attrs={"name": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def parse_pubdate(raw: str | None) -> datetime:
    """Parse article:published_time (date-only or full ISO 8601) into a tz-aware datetime."""
    if not raw:
        return datetime.now(timezone.utc)
    raw = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(raw[:10], fmt)
                break
            except ValueError:
                continue
        else:
            return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def absolutize(soup_fragment: BeautifulSoup, base: str) -> None:
    """Rewrite relative href/src in the article body to absolute URLs, so they survive syndication."""
    for attr in ("href", "src"):
        for tag in soup_fragment.find_all(attrs={attr: True}):
            val = tag[attr].strip()
            if val.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            tag[attr] = urljoin(base, val)


def extract_post(html_path: Path) -> dict | None:
    """Pull the fields the FEED needs from one post file, plus the path (so the
    index step can render its card from the same file via generate_card)."""
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")

    slug = html_path.parent.name
    permalink = meta(soup, prop="og:url") or f"{SITE_URL}/{BLOG_DIR.as_posix()}/{slug}/"

    title = meta(soup, prop="og:title")
    if not title and soup.title:
        title = soup.title.get_text().split("—")[0].strip()
    title = title or slug

    description = meta(soup, prop="og:description") or meta(soup, name="description") or ""
    author = meta(soup, prop="article:author") or "Christian Smith"
    pubdate = parse_pubdate(meta(soup, prop="article:published_time"))

    article = soup.find("article")
    if article is None:
        print(f"  ! skipping {html_path}: no <article> element", file=sys.stderr)
        return None
    body_root = article.find(class_="read-container") or article
    absolutize(body_root, permalink)
    body_html = body_root.decode_contents().strip()

    return {
        "slug": slug,
        "title": title,
        "link": permalink,
        "description": description,
        "author": author,
        "pubdate": pubdate,
        "body": body_html,
        "path": html_path,
    }


def build_item(post: dict) -> str:
    return f"""    <item>
      <title>{escape(post['title'])}</title>
      <link>{escape(post['link'])}</link>
      <guid isPermaLink="true">{escape(post['link'])}</guid>
      <pubDate>{format_datetime(post['pubdate'])}</pubDate>
      <dc:creator>{escape(post['author'])}</dc:creator>
      <description>{escape(post['description'])}</description>
      <content:encoded><![CDATA[{post['body']}]]></content:encoded>
    </item>"""


def write_index(posts: list[dict]) -> None:
    """Regenerate the post-card region of blog/index.html, newest-first, using
    generate_card's renderer so cards match the agent's exactly. The page shell
    outside the markers is never touched."""
    if not INDEX_FILE.exists():
        print(f"  ! {INDEX_FILE} not found; skipping index regeneration", file=sys.stderr)
        return
    html = INDEX_FILE.read_text(encoding="utf-8")
    if POSTS_START not in html or POSTS_END not in html:
        print(f"  ! markers not found in {INDEX_FILE}; skipping index regeneration", file=sys.stderr)
        return
    try:
        template = gc.read(gc.find_template(None))
    except SystemExit as e:
        # find_template exits if the template is missing; don't take the feed down with it.
        print(f"  ! {e}; skipping index regeneration", file=sys.stderr)
        return

    cards = []
    for p in posts:
        ph = gc.read(str(p["path"]))
        cards.append(gc.fill_card(
            template,
            slug=gc.extract_slug(ph),
            date=gc.pretty_date(ph),
            minutes=gc.read_minutes(ph, 200),
            title=gc.extract_title(ph),
            summary=gc.pick_summary(ph, None),
        ))
    block = "\n\n".join(cards)
    before = html.split(POSTS_START)[0]
    after = html.split(POSTS_END, 1)[1]
    INDEX_FILE.write_text(
        f"{before}{POSTS_START}\n{block}\n      {POSTS_END}{after}", encoding="utf-8"
    )
    print(f"Wrote {INDEX_FILE} with {len(cards)} card(s)")


def discover_static_pages() -> list[str]:
    """Find the non-blog pages that belong in the sitemap.

    Scans the repo root and every top-level directory for an index.html, then
    keeps a page only if it declares an og:url and is NOT a redirect stub. The
    og:url is the page's own canonical, which is the same field the feed already
    trusts for posts; using it here keeps one definition of "this page's URL".

    Blog posts live at blog/<slug>/index.html (depth 2) and are handled by the
    feed pass, so this depth-1 glob never double-counts them. blog/index.html
    itself IS picked up here, which is correct: the listing page is a real page.
    """
    candidates = [Path("index.html")] + [
        f for f in sorted(Path(".").glob("*/index.html"))
        if f.parent.name not in SKIP_DIRS
    ]
    urls: list[str] = []
    for f in candidates:
        if not f.is_file():
            continue
        soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
        if soup.find("meta", attrs={"http-equiv": re.compile("^refresh$", re.I)}):
            print(f"  - sitemap: skipping {f} (redirect stub)")
            continue
        url = meta(soup, prop="og:url")
        if not url:
            print(f"  ! sitemap: skipping {f} (no og:url)", file=sys.stderr)
            continue
        urls.append(url.rstrip("/") + "/" if url != SITE_URL else SITE_URL + "/")
    return urls


def write_sitemap(posts: list[dict], pages: list[str]) -> None:
    """Write sitemap.xml from the same parse the feed used.

    Posts carry a real lastmod (article:published_time). Static pages do not
    expose a trustworthy last-modified date, and a wrong lastmod is worse than
    none, so those entries omit it rather than inventing one.
    """
    seen: set[str] = set()
    entries: list[str] = []

    for url in pages:
        if url in seen:
            continue
        seen.add(url)
        entries.append(f"  <url>\n    <loc>{escape(url)}</loc>\n  </url>")

    for post in posts:
        url = post["link"]
        if url in seen:
            continue
        seen.add(url)
        lastmod = post["pubdate"].date().isoformat()
        entries.append(
            f"  <url>\n    <loc>{escape(url)}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n  </url>"
        )

    body = "\n".join(entries)
    SITEMAP.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n",
        encoding="utf-8",
    )
    print(f"Wrote {SITEMAP} with {len(entries)} URL(s)")


def write_robots() -> None:
    """Write robots.txt. Generated (not hand-kept) so the sitemap URL stays tied
    to SITE_URL; one constant, one place to change if the domain ever moves."""
    ROBOTS.write_text(
        "# Generated by scripts/build_feed.py - edit the script, not this file.\n"
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    print(f"Wrote {ROBOTS}")


def main() -> int:
    if not BLOG_DIR.is_dir():
        print(f"error: '{BLOG_DIR}' not found — run this from the repo root.", file=sys.stderr)
        return 1

    post_files = sorted(BLOG_DIR.glob("*/index.html"))
    posts = [p for f in post_files if (p := extract_post(f))]
    posts.sort(key=lambda p: p["pubdate"], reverse=True)

    if not posts:
        print("warning: no posts found; writing an empty feed.", file=sys.stderr)

    items = "\n".join(build_item(p) for p in posts)
    now = format_datetime(datetime.now(timezone.utc))

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(SITE_TITLE)}</title>
    <link>{escape(SITE_URL)}</link>
    <description>{escape(SITE_DESCRIPTION)}</description>
    <language>{SITE_LANGUAGE}</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{escape(FEED_URL)}" rel="self" type="application/rss+xml" />
{items}
  </channel>
</rss>
"""
    OUTPUT.write_text(feed, encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(posts)} post(s): {', '.join(p['slug'] for p in posts)}")

    # Same posts, same pass, shared renderer: the index can't drift from the feed.
    write_index(posts)

    # Same parse again: the sitemap can't drift from the feed either.
    write_sitemap(posts, discover_static_pages())
    write_robots()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
