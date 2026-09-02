#!/usr/bin/env python3
"""Align rnvizion.github.io with the résumé as rebuilt on 2026-08-31.

Run from the repo root of rnvizion.github.io, on a clean checkout of main:

    python align_site_to_resume.py          # apply
    python align_site_to_resume.py --check  # report only, write nothing

Exact-string edits, each guarded with count == 1, per this repo's standing rule.
Every guard sits on the line that does something, never on a comment about it.
A guard that trips means the live file moved since these strings were fetched:
stop and re-fetch rather than loosening it.

What this retires, and why (each is the résumé rule applied to the site):
  - the toolkit's "786 tests, ~76% coverage" — a coverage percentage is an
    approximation, and it is the one figure here that reads as a measurement
    rather than a decision
  KEPT, on purpose, after reading rnv-brand/profile.json (v1.3.1) and the checker:
  - "5,000+" on index.html and resume/index.html. facts.tests names both files as
    sources and fails the Monday drift run if the literal is absent; the figure is
    a source-derived floor that moves only on a decision (ladder: 5,000+ -> 10,000+),
    and scripts/generate_site_og.py renders og-image.png from the stat tiles, so
    a changed tile changes the share image too.
  - AIII's "46 tests" — frozen by decision #4 per the manifest's OpenSSF note;
    it changes only on a commit and is ruled safe published.
  - "four tools" on the publishing agent — it exposes six, and the homepage card
    also credited the agent with rendering the index card and OG image, which the
    agent's own README says CI does, not the agent
  - "AI Engineer" leading the target-roles line — Solutions Engineer leads now
  - remote-only availability — remote or DMV hybrid, clearance-eligible
  - the Excalibur Group entry — three months, overlapping Hotbox, and its
    certificate already sits in Certifications
"""
import sys
from pathlib import Path

CHECK = "--check" in sys.argv
changed = {}


def edit(path: str, old: str, new: str, what: str) -> None:
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    n = s.count(old)
    # Already applied: the old text is gone and the new text is present exactly
    # once. A removal has no new text, so its "present" condition is absence.
    if n == 0 and (new == "" or s.count(new) == 1):
        print(f"  skip  {path}: {what} (already applied)")
        return
    assert n == 1, f"{path}: expected exactly one match for [{what}], found {n} — file has moved, re-fetch"
    if not CHECK:
        p.write_text(s.replace(old, new), encoding="utf-8")
    changed.setdefault(path, []).append(what)
    print(f"  {'would' if CHECK else 'ok   '} {path}: {what}")


# ============================================================================
# resume/index.html
# ============================================================================
R = "resume/index.html"

edit(R,
     '<p class="tagline">Building production AI systems, and the developer tools they run on. AR/VR specialist at Meta.</p>',
     '<p class="tagline">Solutions engineer profile: production AI systems, published where anyone can inspect them, and demonstrated to the people who have to trust them.</p>\n'
     '        <p class="tagline" style="font-size:.92em;opacity:.85">Remote (US) · open to hybrid in the Washington DC metro · U.S. Citizen, able to obtain a security clearance</p>',
     "tagline leads with the profile, not the retail title; availability line added")

edit(R,
     '<p class="summary">Python developer building production AI systems on the Claude API, with nine shipped projects and 5,000+ tests across the portfolio. I build and publish Model Context Protocol servers, including one in the official MCP registry that implements OAuth 2.1 with RFC 9728 protected-resource metadata and enforced per-tool scopes, alongside a retrieval-augmented assistant and an agentic publishing pipeline. Hands-on AR/VR product experience at Meta and a Bachelor of Science in Game Programming, with a proven track record of turning complex technical concepts into clear documentation, training content, and live customer engagement. Targeting remote AI Engineer, Solutions Engineer, and Developer Advocate roles where building, communicating, and shipping production systems all matter.</p>',
     '<p class="summary">I build production AI systems, publish them where anyone can inspect them, and demonstrate them to the people who have to trust them. My color-computation server is published to the official Model Context Protocol registry and listed in awesome-mcp-servers; AIII, my agent identity and authorization reference implementation, ships Sigstore-signed releases, a CycloneDX SBOM, and an OpenSSF Best Practices Baseline self-assessment at 20 of 21 controls with the exception documented rather than hidden. Quality is gated on published thresholds enforced in CI, not on assurances. Four years customer-facing at the technical end: live AR/XR demonstration and tier-1/tier-2 escalation at Meta, enterprise help desk and productivity consulting before that. Nine shipped projects and 5,000+ tests across the portfolio, every project under cross-platform CI with its quality gates published rather than asserted. Targeting Solutions Engineer, Solutions Architect, and Sales Engineer roles at AI and developer-tools companies.</p>',
     "summary: MCP registry first, SE roles lead; 5,000+ kept (facts.tests source)")

edit(R,
     'FastMCP server exposing four tools, orchestrated by a Claude agent loop to automate an end-to-end content-publishing workflow; built and tested in GitHub Codespaces.',
     'FastMCP server exposing six tools, orchestrated by a Claude agent loop that publishes to a live site: validate the post, commit and push, poll until the URL returns 200, then update the retrieval corpus. The model makes one decision — publish or don’t — and deterministic code executes the chain, stopping at the first failure. The orchestration is code, not a prompt, and the dry run is the default. Refusal behavior is pinned by a test suite; a self-contained demo runs the real chain against throwaway git repositories with no credentials or network, and CI runs both on every push.',
     "publishing agent: six tools, and the claims that are now true")

edit(R,
     '            <li>Drive in-store sales and customer education across the full Meta spatial computing lineup, including Ray-Ban Meta smart glasses and the Meta Quest VR headset family, through live product demonstrations and consultative selling.</li>\n'
     '            <li>Provide tier-1 and tier-2 technical support spanning hardware setup, controller pairing, mobile app integration, Meta account configuration, firmware updates, connectivity troubleshooting, and immersive content onboarding.</li>\n'
     '            <li>Translate complex AR, VR, and mixed-reality concepts into clear, accessible explanations for non-technical customers, drawing on a background in technical documentation and content development.</li>\n'
     '            <li>Surface recurring customer pain points and product feedback across both AR and VR product lines to inform onboarding improvements and reduce support friction.</li>',
     '            <li>Run live technical demonstrations of the full Meta spatial computing lineup — Ray-Ban Meta smart glasses and the Quest headset family — translating AR, VR, and mixed-reality architecture into terms non-technical buyers can act on.</li>\n'
     '            <li>Own tier-1 and tier-2 escalation across hardware setup, mobile app integration, account and identity configuration, firmware updates, and connectivity troubleshooting; resolve at the point of contact rather than handing off.</li>\n'
     '            <li>Act as the technical voice in the buying conversation: qualify what the customer is actually trying to do, map it to product capability, and say plainly when the fit isn’t there.</li>\n'
     '            <li>Surface recurring failure patterns and product feedback across both lines to inform onboarding improvements and reduce downstream support load.</li>',
     "Meta bullets: lead with the solutions motion")

edit(R,
     '        <div class="entry">\n'
     '          <div class="entry-head"><span class="org">The Excalibur Group</span><span class="date">Mar 2024 – May 2024</span></div>\n'
     '          <div class="entry-sub"><span class="role">Google IT Support Specialist Trainee</span><span class="loc">Washington, DC</span></div>\n'
     '          <ul>\n'
     '            <li>Completed intensive Google IT Support training covering Google Workspace, Google Cloud Platform, Android OS, network fundamentals, and incident management.</li>\n'
     '            <li>Documented and analyzed technical issues using structured troubleshooting frameworks, reinforcing foundational systems administration and customer-facing support skills.</li>\n'
     '          </ul>\n'
     '        </div>\n'
     '\n',
     '',
     "Excalibur Group entry removed (overlapping three-month trainee stint)")

edit(R,
     '11 transformation modes, 9+ file formats, regex builder, folder watching, full CLI. 786 tests, ~76% coverage, CI on Linux + Windows.',
     '11 transformation modes, 9+ file formats, regex builder, folder watching, full CLI. CI on Linux + Windows.',
     "Text Transformer: test count and coverage retired")

# ============================================================================
# index.html
# ============================================================================
H = "index.html"

edit(H,
     '          Open to remote AI Engineer, Solutions Engineer &amp; Developer Advocate roles',
     '          Open to Solutions Engineer &amp; AI Engineer roles · remote or DMV hybrid',
     "hero: Solutions Engineer leads; availability widened")

edit(H,
     'A FastMCP server exposes four tools; a Claude loop drives them end to end, validating a post\'s metadata, generating its index card and Open Graph image, committing and pushing, then waiting for the page to go live before updating the corpus behind Ask the Corpus. The irreversible publish step sits behind its own gate, and anything that fails validation doesn\'t ship.',
     'A FastMCP server exposes six tools; a Claude loop makes one decision — publish or don’t — and deterministic code runs the chain: validate the post, commit and push, poll until the page is live, then update the corpus behind Ask the Corpus. The index, feed, and Open Graph image are built by CI on the push, not by the agent. The dry run is the default, anything that fails validation doesn’t ship, and the refusal behavior is pinned by a test suite that runs on every commit.',
     "publishing agent card: six tools; agent no longer credited with CI's work")

edit(H,
     'Backed by 786 tests at ~76% coverage running on Linux and Windows CI.',
     'Runs on Linux and Windows CI.',
     "Text Transformer card: test count and coverage retired")

edit(H,
     '<p>Open to remote AI Engineer, Solutions Engineer, and Developer Advocate roles. Always happy to talk production AI, developer tooling, or the craft of building things that feel right.</p>',
     '<p>Open to Solutions Engineer, AI Engineer, implementation, and technical account roles; remote, or hybrid in the DMV. Always happy to talk production AI, developer tooling, or the craft of building things that feel right.</p>',
     "contact: Solutions Engineer leads; availability widened")

# ============================================================================
# bio/index.html
# ============================================================================
B = "bio/index.html"

edit(B,
     'Each ships with CLI support, multi-theme UIs, cross-platform CI, and comprehensive test coverage; 786 tests on the text transformer alone, and more than 5,000 across the whole portfolio. They\'re where',
     'Each ships with CLI support, multi-theme UIs, cross-platform CI, and comprehensive test coverage; more than 5,000 tests across the whole portfolio. They\'re where',
     "toolkit: 786 retired; the portfolio floor stays")

edit(B,
     '<p>Christian is open to remote AI Engineer, Solutions Engineer, and Developer Advocate roles; positions where he can build, communicate, and ship production systems at once, and where the job is as much translation as it is code.</p>',
     '<p>Christian is open to Solutions Engineer, AI Engineer, implementation, and technical account roles, remote or hybrid in the DMV; positions where he can build, communicate, and ship production systems at once, and where the job is as much translation as it is code.</p>',
     "open-to line: Solutions Engineer leads; availability widened")

# ============================================================================
print()
if CHECK:
    print(f"check only — {sum(len(v) for v in changed.values())} edits would apply across {len(changed)} files; nothing written")
else:
    print(f"applied {sum(len(v) for v in changed.values())} edits across {len(changed)} files")
    for f in changed:
        print(f"  {f}")
    print("\nnext: git diff --stat, read it, then commit.")
