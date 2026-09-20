#!/usr/bin/env python3
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

THE RULE ITSELF LIVES IN _templates/post-template.RULES.md, under "What a post
consists of". The two functions that implement it live in scripts/post_shape.py,
which the publishing agent imports rather than reimplements -- so this file
tests a library it shares rather than one it owns. Hence check 0: importing that
module must do nothing, because an import-time side effect here is a dead
publish over there.

Run: python tests/test_post_shape.py
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# 0. The import contract, and it runs BEFORE this file imports the library.
#    The agent imports post_shape into a live publish, so anything that module
#    does at import time runs inside that process. Probed in a subprocess
#    because an import cannot be observed twice -- and probed first, because a
#    side effect fatal enough to matter is fatal enough to kill this file's own
#    import and take the report with it. Checking after the import can only
#    catch the harmless cases.
#
#    Bought with a demonstration rather than an argument: before the split,
#    importing the guard ran the whole tree walk and exited the caller -- over
#    a defect in a different post than the one being published.
_probe = subprocess.run(
    [sys.executable, "-c",
     "import sys; sys.path.insert(0, %r); import post_shape; "
     "print('NAMES', hasattr(post_shape, 'sibling_refs'), "
     "hasattr(post_shape, 'shown_outside_code'))" % str(ROOT / "scripts")],
    capture_output=True, text=True, cwd=str(ROOT))
if _probe.returncode != 0 or _probe.stdout.strip() != "NAMES True True":
    print("POST SHAPE FAILED")
    print()
    print("  scripts/post_shape.py broke its import contract.")
    print("  It must import silently, exit 0, and expose sibling_refs and")
    print("  shown_outside_code. The publishing agent imports it mid-publish;")
    print("  anything it does on import happens inside that process.")
    print()
    print("    exit code: %d" % _probe.returncode)
    print("    stdout:    %r" % _probe.stdout.strip()[:300])
    if _probe.stderr.strip():
        print("    stderr:    %s" % _probe.stderr.strip().splitlines()[-1][:200])
    sys.exit(1)

from post_shape import shown_outside_code, sibling_refs  # noqa: E402









def tracked(pattern):
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", pattern],
        capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p.strip()]






VECTORS = ROOT / "tests/fixtures/post-shape-vectors.json"
LIB = ROOT / "scripts/post_shape.py"
vector_count = 0

failures = []

# 1. The vectors. They are written by hand as an independent statement of
#    what the rule means -- never derived from this file -- because a test that
#    reads its expectations out of the thing it tests cannot detect a change to
#    that thing -- and this file now tests a shared library, which is exactly
#    when a contract test earns its place.
if not VECTORS.exists():
    failures.append("%s is missing; the vectors are this library's contract "
                    "test and the agent imports the library" % VECTORS.name)
else:
    import json
    loaded = json.loads(VECTORS.read_text(encoding="utf-8"))["vectors"]
    vector_count = len(loaded)
    for vector in loaded:
        for label, fn, key in (("refs", sibling_refs, "catches"),
                               ("shown", shown_outside_code, "shows")):
            want = sorted(vector.get(key, []))
            got = sorted(fn(vector["html"]))
            if got != want:
                failures.append(
                    "vector %s [%s]: expected %s, got %s -- %s"
                    % (vector["id"], label, want, got, vector["why"]))

posts = tracked("blog/*/index.html")
if not posts:
    failures.append("no posts found under blog/ -- has the layout moved?")

# 2. Nothing under blog/ is anything but an index.html.
for path in tracked("blog/*"):
    if not path.endswith("/index.html"):
        failures.append(
            "%s is tracked under blog/ and is not an index.html; a publish "
            "commits one path and would not carry it" % path)

# 3. Each post folder holds exactly one tracked file.
for post in posts:
    folder = post.rsplit("/", 1)[0]
    siblings = [p for p in tracked(folder + "/*") if p != post]
    if siblings:
        failures.append(
            "%s/ holds %d file(s) beside index.html: %s"
            % (folder, len(siblings), ", ".join(siblings)))

# 4. No post references a path that resolves inside its own folder. This one
#    fires before the sibling is committed, which is the case checks 2 and 3
#    cannot see -- and it is the case that actually reaches a reader.
# 5. Markup shown to a reader sits in <code> or <pre>. Checked in the same pass
#    so the two are never confused: escaped markup in a bare <p> is a wrapper
#    mistake, and reporting it as a missing file sends the author looking for
#    something that was never meant to exist.
for post in posts:
    html = (ROOT / post).read_text(encoding="utf-8")
    for ref in sibling_refs(html):
        failures.append(
            "%s references %r, which resolves beside the post; a publish "
            "carries the html only" % (post, ref[:80]))
    for shown in shown_outside_code(html):
        failures.append(
            "%s shows %r outside <code>/<pre>; wrap it, per \"What a post "
            "consists of\" in _templates/post-template.RULES.md"
            % (post, shown[:60]))

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

print("post shape OK: %d post(s); one tracked file each, no sibling refs, "
      "no unwrapped markup; %d vector(s) green, import clean"
      % (len(posts), vector_count))
