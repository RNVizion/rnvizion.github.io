#!/usr/bin/env python3
"""Homepage pass 2 for rnvizion.github.io — index.html, plus the résumé page's meta descriptions.

Built from: rnvizion.github.io main as fetched 2026-09-02, after
align_site_to_resume.py landed (verified byte-identical to the checked copy).

Run from the repo root, on a clean checkout of main:

    python homepage_pass2.py          # apply
    python homepage_pass2.py --check  # report only, write nothing

Same rules as the first script: exact-string edits, count == 1 guards, a guard
that trips means the file moved — re-fetch, never loosen.

What it does:
  1. About, third paragraph: the roles line still read "remote AI Engineer and
     Solutions Engineer roles". The first script's grep looked for "Open to remote"
     and this sentence does not start that way. Same fix as the hero and contact.
  2. Hero subtitle: led with "Python developer" and closed on the retail title.
     Rewritten to the solutions-engineer framing; keeps the manifest's tagline stem
     ("production AI systems"), which is the only thing profile.json asserts here.
  3. Featured essays: the three cards were the three oldest posts (May–June). Swapped
     for Honest and Wrong, The Margin, Not the Price, and Fit Over Default, with each
     card's blurb taken verbatim from blog/index.html rather than rewritten.
  4. Meta descriptions on both pages (description, og:description, twitter:description)
     still opened "Python developer" and closed on the retail title. These are the text
     of the preview card when rnvizion.dev is pasted into a LinkedIn message or an
     email, which is the audience this week. Titles are left alone; the OG generator
     reads og:title, not the descriptions, so the share images do not change.

What it deliberately does not touch: the stat tiles (facts.tests and facts.projects
read them, and generate_site_og.py renders og-image.png from them), the AIII card's
46 tests (decision #4), and the canonical author bio.

build-og.yml has index.html in its path filter, so this commit re-renders the share
image; the tiles are unchanged, so the image should come back identical.
"""
import sys
from pathlib import Path

CHECK = "--check" in sys.argv
changed = {}


def edit(path: str, old: str, new: str, what: str) -> None:
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    n = s.count(old)
    if n == 0 and (new == "" or s.count(new) == 1):
        print(f"  skip  {path}: {what} (already applied)")
        return
    assert n == 1, f"{path}: expected exactly one match for [{what}], found {n} — file has moved, re-fetch"
    if not CHECK:
        p.write_text(s.replace(old, new), encoding="utf-8")
    changed.setdefault(path, []).append(what)
    print(f"  {'would' if CHECK else 'ok   '} {path}: {what}")


H = "index.html"

edit(H,
     "I'm targeting remote AI Engineer and Solutions Engineer roles where building, communicating, and shipping production systems all matter.</p>",
     "I'm targeting Solutions Engineer and AI Engineer roles, remote or hybrid in the DMV, where building, communicating, and shipping production systems all matter.</p>",
     "About: roles line — Solutions Engineer leads; availability widened")

edit(H,
     '<p class="hero-subtitle">Python developer building production AI on the Claude API: retrieval systems held to a CI-gated eval suite, LLM agents, and an MCP server any model can call. I ship polished developer tools, and I write about the craft. AR/VR specialist at Meta by day.</p>',
     '<p class="hero-subtitle">I build production AI systems and demonstrate them to the people who have to trust them: retrieval held to a CI-gated eval suite, LLM agents, and an MCP server any model can call. I ship polished developer tools, and I write about the craft. AR/VR at Meta by day.</p>',
     "hero subtitle: solutions-engineer framing; tagline stem kept")

edit(H,
     '          <article class="writing-card">\n'
     '            <span class="essay-tag">Essay</span>\n'
     '            <h3>I Lacked the Tools, So I Built Them</h3>\n'
     '            <p>On constraint as a creative force: why the gap between what you have and what you need is an invitation, not a wall.</p>\n'
     '            <a class="project-link" href="/blog/i-lacked-the-tools/" target="_self">Read it →</a>\n'
     '          </article>\n'
     '          <article class="writing-card">\n'
     '            <span class="essay-tag">Essay</span>\n'
     '            <h3>Squish</h3>\n'
     '            <p>The human decision that turns software from working into loved; the soul that speed alone can\'t generate.</p>\n'
     '            <a class="project-link" href="/blog/squish/" target="_self">Read it →</a>\n'
     '          </article>\n'
     '          <article class="writing-card">\n'
     '            <span class="essay-tag">Essay</span>\n'
     '            <h3>Lazy in the Right Way Is Leverage</h3>\n'
     '            <p>Strategic economy of effort: doing less on purpose, so the energy lands where it actually moves the work.</p>\n'
     '            <a class="project-link" href="/blog/sloth/" target="_self">Read it →</a>\n'
     '          </article>',
     '          <article class="writing-card">\n'
     '            <span class="essay-tag">Essay</span>\n'
     '            <h3>Honest and Wrong</h3>\n'
     '            <p>It told me eight. The answer was nine. It wasn’t hallucinating; it was counting.</p>\n'
     '            <a class="project-link" href="/blog/honest-and-wrong/" target="_self">Read it →</a>\n'
     '          </article>\n'
     '          <article class="writing-card">\n'
     '            <span class="essay-tag">Essay</span>\n'
     '            <h3>The Margin, Not the Price</h3>\n'
     '            <p>Everyone keeps quoting the line about charging more. The price isn’t what moves; the margin is.</p>\n'
     '            <a class="project-link" href="/blog/the-margin-not-the-price/" target="_self">Read it →</a>\n'
     '          </article>\n'
     '          <article class="writing-card">\n'
     '            <span class="essay-tag">Essay</span>\n'
     '            <h3>Fit Over Default</h3>\n'
     '            <p>The reflex is to grab the biggest model. I built two systems and chose the opposite on purpose; here&#8217;s why fit beats default.</p>\n'
     '            <a class="project-link" href="/blog/fit-over-default/" target="_self">Read it →</a>\n'
     '          </article>',
     "featured essays: the three oldest replaced with Honest and Wrong / The Margin, Not the Price / Fit Over Default")

# ---- meta descriptions: what a pasted link shows before anyone clicks ----
NEW_HOME = ("I build production AI systems and demonstrate them to the people who have to trust them: "
            "RAG with CI-gated evals, LLM agents, and an MCP server in the official registry with OAuth 2.1. "
            "Open to Solutions Engineer and AI Engineer roles; remote or DMV hybrid.")

edit(H,
     '<meta name="description" content="Christian Smith (RNVizion): Python developer building production AI systems on the Claude API: RAG with CI-gated evals, LLM agents, and an MCP server in the official registry with OAuth 2.1; plus a suite of polished developer tools. AR/VR specialist at Meta." />',
     '<meta name="description" content="Christian Smith (RNVizion): ' + NEW_HOME + '" />',
     "meta description: solutions-engineer framing; retail title dropped")

edit(H,
     '<meta property="og:description" content="Python developer building production AI systems on the Claude API: RAG with CI-gated evals, LLM agents, and an MCP server in the official registry with OAuth 2.1. AR/VR specialist at Meta." />',
     '<meta property="og:description" content="' + NEW_HOME + '" />',
     "og:description: same text")

edit(H,
     '<meta name="twitter:description" content="Python developer building production AI systems on the Claude API: RAG with CI-gated evals, LLM agents, and an MCP server in the official registry with OAuth 2.1. AR/VR specialist at Meta." />',
     '<meta name="twitter:description" content="' + NEW_HOME + '" />',
     "twitter:description: same text")

R = "resume/index.html"
NEW_RES = ("solutions engineer profile; production AI systems published where anyone can inspect them: "
           "a CI-gated RAG assistant, an agentic publishing pipeline, and an MCP server in the official registry with OAuth 2.1. "
           "Remote or DMV hybrid.")

edit(R,
     '<meta name="description" content="The résumé of Christian “RNVizion” Smith — Python developer building production AI systems on the Claude API: a CI-gated RAG assistant, an agentic publishing pipeline, and an MCP server in the official registry with OAuth 2.1. AR/VR specialist at Meta." />',
     '<meta name="description" content="The résumé of Christian “RNVizion” Smith — ' + NEW_RES + '" />',
     "résumé meta description: matches the page's new tagline")

edit(R,
     '<meta property="og:description" content="Python developer building production AI on the Claude API: a CI-gated RAG assistant, an agentic publishing pipeline, and an MCP server in the official registry with OAuth 2.1. AR/VR specialist at Meta." />',
     '<meta property="og:description" content="Christian Smith — ' + NEW_RES + '" />',
     "résumé og:description: same text")

# ---- OpenSSF wording: conform to the recorded ruling ----
# profile.json manual_surfaces["OpenSSF Best Practices Baseline"] rules the phrase:
# "a submission at a count, never a passing badge. Keep that wording." The summary
# rewritten in pass 1 said "self-assessment", which left resume/index.html carrying
# BOTH wordings — the summary and the AIII entry four hundred lines apart — and put
# one of them outside a ruling this project does not own. Conform rather than argue;
# whether "self-assessment" is the more precise word is a question for the manifest's
# owner, and it travels as a note.
edit(R,
     'an OpenSSF Best Practices Baseline self-assessment at 20 of 21 controls with the exception documented rather than hidden',
     'an OpenSSF Best Practices Baseline submission at 20 of 21 controls with the exception documented rather than hidden',
     "OpenSSF: \"self-assessment\" -> \"submission\" per the manifest ruling; page now self-consistent")

print()
if CHECK:
    print(f"check only — {sum(len(v) for v in changed.values())} edits would apply; nothing written")
else:
    print(f"applied {sum(len(v) for v in changed.values())} edits across {len(changed)} file(s): {', '.join(changed) or 'nothing'}")
    print("\nnext: git diff --stat, read it, then commit. build-og will re-render og-image.png; expect it unchanged.")
