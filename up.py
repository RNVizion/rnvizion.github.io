#!/usr/bin/env python3
"""shape.py -- install the post-shape guard and wire it into build-feed.

Adds tests/test_post_shape.py and one CI step beside the existing gates. The
step name and the test path are written here once; nothing else in the repo
moves.

Guarded: the anchor must appear exactly once, and the assertion is on the CI
step that runs a gate, never on a comment that mentions one -- a script that
describes what it inserts will find its own description otherwise.

Re-running is a no-op: if the step is already present the script says so and
exits 0 without touching anything.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, check=True).stdout.strip())

WORKFLOW = ROOT / ".github/workflows/build-feed.yml"
TEST = ROOT / "tests/test_post_shape.py"

ANCHOR = (
    "      - name: Template pairing\n"
    "        run: python tests/test_template_pairing.py\n"
)
ADDITION = (
    "\n"
    "      # Gate: the publishing agent commits exactly blog/<slug>/index.html.\n"
    "      # If a post gains a sibling file, that commit would drop it silently.\n"
    "      - name: Post shape\n"
    "        run: python tests/test_post_shape.py\n"
)
STEP_KEY = "        run: python tests/test_post_shape.py\n"

TEST_BODY = r'''#!/usr/bin/env python3
"""A post is one tracked file, and it references nothing beside itself.

The publishing agent builds one commit carrying exactly blog/<slug>/index.html.
That is lossless only while a post IS that one path. If a post ever gains a
sibling -- an image, a per-post stylesheet, a script -- the publish pushes the
HTML and silently drops the rest, and the post goes live referencing files that
are not there.

The agent asked to be told in the same change if what a post consists of ever
changes. An obligation on nobody in particular fires into an empty room, so it
is attached to the event instead: build-feed.yml already triggers on blog/**,
so this runs on the publish commit itself.

An OG card is not a counterexample. Every post references one, but by absolute
URL under /assets/, committed by build-og on a different path. The post's second
file has a second writer. That is what makes one path enough -- not that a post
is simple, but that nothing it needs is waiting on the publish to carry it.

A FAILURE HERE IS NOT A BUG TO SILENCE. It means a post's shape changed, which
is exactly the moment the agent chat needs a note; its staged set has to move in
the same change. Fix the post, or send the note and widen this test with it.

Run: python tests/test_post_shape.py
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Schemes and roots that resolve somewhere other than the post's own folder.
# Whatever is left is a sibling, which is the whole point of this test.
ELSEWHERE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|/|#)", re.I)

# Attributes the browser fetches, plus CSS url(). Deliberately NOT a blanket
# content= sweep: most meta content is prose, and a check that fires on a page
# title is one somebody turns off.
REFS = re.compile(
    r"""(?:\bsrc|\bhref|\bposter|\bdata-src|\bsrcset)\s*=\s*["']([^"']+)["']"""
    r"""|\burl\(\s*["']?([^"')]+)["']?\s*\)""",
    re.I,
)

# A self-contained payload carries its own url() and quotes; scanning inside it
# reports references to things that are not files.
DATA_URI = re.compile(
    r"""url\(\s*(["'])\s*data:.*?\1\s*\)|(?:\bsrc|\bhref)\s*=\s*(["'])data:.*?\2""",
    re.I | re.S,
)

META = re.compile(r"<meta\b[^>]*>", re.I)
META_KEY = re.compile(r"""\b(?:property|name)\s*=\s*["']([^"']+)["']""", re.I)
META_VAL = re.compile(r"""\bcontent\s*=\s*["']([^"']+)["']""", re.I)
IMAGE_KEYS = {"og:image", "og:image:url", "og:image:secure_url", "twitter:image",
              "twitter:image:src", "og:audio", "og:video"}


def tracked(pattern):
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", pattern],
        capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p.strip()]


def sibling_refs(html):
    """Every reference in the document that resolves inside the post's folder."""
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    html = DATA_URI.sub(" ", html)
    found = []
    for match in REFS.finditer(html):
        ref = (match.group(1) or match.group(2) or "").strip()
        if ref and not ELSEWHERE.match(ref):
            found.append(ref)
    for tag in META.findall(html):
        key = META_KEY.search(tag)
        val = META_VAL.search(tag)
        if key and val and key.group(1).lower() in IMAGE_KEYS:
            ref = val.group(1).strip()
            if ref and not ELSEWHERE.match(ref):
                found.append(ref)
    return found


failures = []

posts = tracked("blog/*/index.html")
if not posts:
    failures.append("no posts found under blog/ -- has the layout moved?")

# 1. Nothing under blog/ is anything but an index.html.
for path in tracked("blog/*"):
    if not path.endswith("/index.html"):
        failures.append(
            "%s is tracked under blog/ and is not an index.html; a publish "
            "commits one path and would not carry it" % path)

# 2. Each post folder holds exactly one tracked file.
for post in posts:
    folder = post.rsplit("/", 1)[0]
    siblings = [p for p in tracked(folder + "/*") if p != post]
    if siblings:
        failures.append(
            "%s/ holds %d file(s) beside index.html: %s"
            % (folder, len(siblings), ", ".join(siblings)))

# 3. No post references a path that resolves inside its own folder. This one
#    fires before the sibling is committed, which is the case checks 1 and 2
#    cannot see -- and it is the case that actually reaches a reader.
for post in posts:
    for ref in sibling_refs((ROOT / post).read_text(encoding="utf-8")):
        failures.append(
            "%s references %r, which resolves beside the post; a publish "
            "carries the html only" % (post, ref[:80]))

if failures:
    unique = sorted(set(failures))
    print("POST SHAPE FAILED")
    print()
    for f in unique[:20]:
        print("  " + f)
    if len(unique) > 20:
        print("  ... and %d more" % (len(unique) - 20))
    print()
    print("A post is blog/<slug>/index.html and nothing else. If that is")
    print("changing on purpose, the publishing agent's staged set has to move")
    print("in the same change -- send the note, then widen this test.")
    sys.exit(1)

print("post shape OK: %d post(s), one tracked file each, no sibling refs" % len(posts))
'''


def main():
    if not WORKFLOW.exists():
        sys.exit("build-feed.yml not found at %s" % WORKFLOW)

    yaml_text = WORKFLOW.read_text(encoding="utf-8")

    if STEP_KEY in yaml_text and TEST.exists():
        print("already installed -- nothing to do.")
        return 0

    n = yaml_text.count(ANCHOR)
    assert n == 1, (
        "expected the pairing step exactly once in build-feed.yml, found %d. "
        "The workflow has moved; re-cut this script against live." % n)
    assert STEP_KEY not in yaml_text, (
        "build-feed.yml already runs the post-shape test but the test file is "
        "missing; fix by hand rather than letting this script guess.")

    TEST.parent.mkdir(parents=True, exist_ok=True)
    TEST.write_text(TEST_BODY, encoding="utf-8")
    print("wrote %s (%d bytes)" % (TEST.relative_to(ROOT), len(TEST_BODY)))

    updated = yaml_text.replace(ANCHOR, ANCHOR + ADDITION, 1)
    assert updated != yaml_text, "anchor matched but replacement was a no-op"
    WORKFLOW.write_text(updated, encoding="utf-8")
    print("wired the step into %s" % WORKFLOW.relative_to(ROOT))

    try:
        import yaml
        yaml.safe_load(updated)
        print("workflow parses")
    except ImportError:
        print("pyyaml not installed -- workflow not parse-checked")

    print()
    print("running the guard against the live tree:")
    r = subprocess.run([sys.executable, str(TEST)])
    if r.returncode != 0:
        print()
        print("The guard fails on the tree as it stands. That is a finding, not")
        print("a bug in the script: read it before committing.")
        return r.returncode

    print()
    print("Commit both files together; the test and its CI step are one change.")
    print('  git add tests/test_post_shape.py .github/workflows/build-feed.yml')
    print('  git commit -m "ci: guard that a post stays one file"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
