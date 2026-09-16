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
