# post-template.RULES.md

**Pairs with `post-template.html`. Same stem, same folder.** The template is the skeleton; this is
the brain. Read this before editing either.

**Why the pair exists.** Posts are published by copying the template, so anything written into the
template ships on every post built from it. Comments explaining a decision are addressed to whoever
edits the template — an audience that never reads a published post's source. Copying them into the
public artifact put the reasoning where nobody could act on it and left eight posts carrying a
private argument about WCAG ratios.

**So neither the template nor a post carries a comment that explains or instructs.** Nothing to strip
after the fact, nothing to drift, nothing to remember at publish time. **It is clean from the start.**

**Four structural markers stay**, because they navigate rather than explain:

```
<!-- Open Graph -->
<!-- Fonts -->
<!-- Blog-index card teaser. -->
<!-- Standing author bio. -->
```

**The line is purpose, not length.** A marker names a section for anyone reading the page. An
explanation is addressed to whoever edits the template and has no audience in a published post.
Two comments used to carry both at once — *"Standing author bio. Ships on every post; keep in sync
with /bio/"* — and were split: the label stayed, the instruction moved here.

**The list is an allowlist, checked exactly, not a rule about brevity.** "Short comments stay" is a
heuristic, and the first four-word instruction would defeat it silently. Adding a fifth marker is a
decision someone makes on purpose.

**The cost, stated plainly.** A comment is already open in front of the person about to make the
mistake; this file has to be opened. Four real errors were prevented by inline comments in the week
before this split — each one sat exactly where someone would do the wrong thing. That protection is
traded for cleanliness, and the trade only works if this file is actually read. **Every "never" below
is here because someone already tried it or nearly did.**

---

## Publishing a new post

1. **Copy the template** to `blog/<your-slug>/index.html`. The folder name is the slug that appears
   in `og:url`.
2. **Replace every `[SQUARE-BRACKET]` placeholder.**
3. **Do not add comments that explain or instruct.** The four structural markers above are the
   whole allowance. If a choice needs explaining, it goes here.

**Four things the feed generator requires. A post missing any of them is broken, not imperfect:**

| | Why |
|---|---|
| `blog/<slug>/index.html` | the folder name *is* the slug in `og:url` |
| `<article> … </article>` | no `<article>`, and the post is **skipped entirely** |
| `article:published_time` | no date and it stamps as *today* and sorts to the top |
| `og:url` | the canonical link dev.to credits back |

**Recommended, and they have fallbacks but set them anyway:** `og:title`, `og:description`,
`article:author`.

**The date is confirmed by you at publish, not inherited from the draft.** A post written on Tuesday
and published on Thursday carries Tuesday's date unless someone moves it, and both
`article:published_time` and the visible `.article-meta` line have to move together.

---

## What a post consists of

**A post is `blog/<slug>/index.html` and nothing else.** One file, one folder, no siblings.

**Why it is a rule and not a habit.** The publishing agent builds one commit carrying that single
path. If a post ever gains a file beside it — an image, a per-post stylesheet, a script — the
publish pushes the HTML and drops the rest without saying so, and the post goes live referencing
files that are not there.

**The OG card is not an exception, and the reason matters.** Every post references one, at
`https://rnvizion.dev/assets/og/<slug>.png`. So a post already consists of two files. What makes one
path enough is not that a post is simple; it is that the second file has a second writer — `build-og`
commits it, on a different path, after the publish. So the condition to watch is narrower than "a
post gained a file":

> **a post gains a file that no other writer commits.**

**The reference rule.** Nothing in a post may reference a path that resolves inside the post's own
folder. Absolute URLs, root-relative paths, protocol-relative URLs, in-page anchors and `data:` URIs
are all fine — each resolves somewhere another writer is responsible for. A bare `hero.png` does not.

**Markup shown to a reader goes inside `<code>` or `<pre>`.** Escaping hides the angle brackets, not
the attributes: a paragraph explaining `&lt;img src="hero.png"&gt;` carries that exact string in the
page bytes without ever fetching anything. Use and mention are identical to a checker, so the
elements that mean *this is being shown* are what tell the two apart, and that is why this is a rule
rather than a style note — it is what makes the reference check possible at all.

**It is enforced, and it reports as itself.** Escaped markup outside `<code>` or `<pre>` fails with
*shows … outside `<code>`/`<pre>`*, pointing back at this section. It does **not** report as a
missing file, which is what it did for the four hours this rule existed unenforced: the check read
the escaped attribute as a real reference and refused the post by naming a file nobody had written.
**A refusal that names the wrong thing is worse than no refusal** — it sends the author looking for a
file that was never meant to exist, and the guard gets read as broken rather than the post.
A comparison in prose (`x &lt; y`) is not markup and is deliberately not matched.

**Who asserts this.** `tests/test_post_shape.py` checks the whole tree in `build-feed`. The
publishing agent checks the reference rule alone, against the one document it is about to push.
Both run `tests/fixtures/post-shape-vectors.json`, which is this repo's file; if the two
implementations ever disagree on a vector, one of them is wrong and the disagreement is legible.
**Agreeing on the vectors is a floor, not a proof** — two parsers can still diverge anywhere no
vector reaches, which is how the vector for two code spans with a live reference between them came
to exist.

**Which check actually prevents anything.** Pages serves the publish commit directly, so by the time
`build-feed` runs, the post is already live: the site's own check is a backstop that reports, not a
gate that stops. The agent holds the irreversible step, so its copy is the one that can turn *post
live, feed stale, workflow red* into *nothing published*. Both are kept. The later one still fires
if the earlier one goes stale.

**If a post ever needs to be more than one file, that is a decision, not a fix.** Tell the
publishing agent in the same change so its staged set moves with it, then widen the test. Do not
loosen either check to make a red build go green.

## The body

**Everything the feed pulls comes from inside `<article>`.** Keep it wrapped exactly as the template
has it.

**The spine:** open on a concrete moment, widen to the framing, turn, sit in the tension, land on the
aphorism.

- The **first paragraph** gets the drop-cap automatically. Open concrete.
- Repeat `<hr />` + `<h2>` + `<p>` blocks for each section.
- The **`.bio` block** near the bottom is the standing author bio. It ships on every post, so treat
  it as brand copy and **keep it in sync with `rnvizion.dev/bio`.**

---

## Meta and cards

**`card:summary` is not `og:description`.** The description is the SEO line; the summary earns the
click, and the blog-index card generator reads it. Keep them distinct.

Use **curly quotes** inside the attribute so it cannot break early. If `card:summary` is omitted the
card falls back to `og:description`, which is worse but not broken.

---

## CSS decisions, by selector

### `article code` — inline code in prose

**Colour is `var(--code)`, this site's mirror of `--rnv-code`, emitted by `engine/brand.py`.** Not
`var(--accent)`. Code had its own hue as of 2026-09-12 precisely so it stops sharing one with links
and `strong`.

**`0.88em` is an optical correction, not a shrink.** Mono carries a larger x-height than Inter at the
same point size, so parity makes code look *bigger* than the text around it. At 17px body this
computes to 14.96px — **normal text** for WCAG, so the floor is 4.5 rather than 3.0.

> **Never add a border to this rule.** One sat here and did nothing: 1.049:1 against its own chip,
> indistinguishable at 4× against the real faces. The chip is 1.147:1 and reads plainly. **Same
> arithmetic, opposite outcome**, because area and stroke width change what a ratio buys. It never
> defined the chip and adding it back to "define" the chip repeats a mistake that was already made
> and measured.

The ratios and the AAA trade are owned by `BRAND_COLORS.md` and `BRAND_TYPE.md`. They are not
repeated here beyond what the rules above need.

### `article p a`, `article li a`, `.bio a` — links in running text

**Underlined at rest.** Gold against body text is 1.517:1 where WCAG 1.4.1 wants 3:1 when colour is
the only cue — and a hover underline is not a cue, because it does not exist on touch and is absent
while the page is being read.

> **Never promote this to a bare `a`.** `nav`, `footer` and `.post-footer-links` are link *regions*:
> position tells a reader they are links, so colour is not doing the work alone there. Underlining
> them is noise with no accessibility gain.

### `.logo .dot` — the nav mark dot

**`flex-shrink: 0` is load-bearing.** `.logo` is a flex container, and without it the dot is squeezed
to an ellipse whenever the nav is tight — which happened on the live site, at every viewport width,
unnoticed through three passes of deliberate work on that component because every pass was about
colour.

**Geometry only.** The gold, the 12px glow and `pulse 2.4s` are unchanged and were ruled separately.

---

## What never comes back

Each of these was tried, measured, and rejected. They are listed together because they are the
things a future editor is most likely to "fix".

| Never | Why |
|---|---|
| A border on `article code` | 1.049:1 — invisible; the chip already separates |
| `color: var(--accent)` on `article code` | code left gold on purpose; it now separates by hue |
| A bare `a { text-decoration: underline }` | link regions do not need it |
| Removing `flex-shrink: 0` from `.logo .dot` | the dot becomes an ellipse |
| Any comment that explains or instructs | that is what this file is |

---

## What ships

**The template ships nothing. Only posts built from it do.** Everything in the template appears in
every post, which is why the template carries no private reasoning.

If a future template gains a companion file, it follows the same convention: **same stem, adjacent,
`.RULES.md`.** The pairing is mechanical so it can be checked — a guard can assert that every
template has one, which is a thing no comment could ever offer.
