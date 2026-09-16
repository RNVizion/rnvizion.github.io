# post-card-template.RULES.md

**Pairs with `post-card-template.html`. Same stem, same folder.** The template is the skeleton; this
is the brain. Read this before editing either.

**Why the pair exists.** The same reason as the post template: anything written into a template is
copied wherever that template goes, and reasoning addressed to whoever edits it has no audience at
the destination. This card block is pasted into `blog/index.html`, so a 22-line instruction comment
was travelling into the blog index on every publish.

**So the template carries no comment that explains or instructs.** Unlike the post template it has
no structural markers to keep — there are no sections to label in a single `<article>` block — so it
carries **no comments at all**.

---

## Publishing a card

1. **Copy the `<article>` block** into the blog index list.
2. **Add it at the TOP.** The index reads newest-first.
3. **Replace every `[SQUARE-BRACKET]` placeholder.**
4. **Do not paste this file's contents, or any comment, along with it.**

---

## Four values that must match the post exactly

The card and the post are two artifacts describing one thing, and nothing checks that they agree.

| Placeholder | Must equal |
|---|---|
| `[POST-SLUG]` | the folder name under `/blog/` — **and the post's `og:url`** |
| `[Month Day, Year]` | the post's `article:published_time`, rendered |
| `[X]` | the read-time shown in the post header |
| `[POST TITLE]` | the post's title **exactly** |

**`[POST TITLE]` is plain text here.** No `<em>`. The post's `<h1>` carries an italic phrase for
emphasis; the card does not, and copying the markup across produces a heading that styles
differently from every other card in the list.

**If the date slips between writing and publishing, three places move together** — the card, the
post's `article:published_time`, and the post's visible `.article-meta` line. Two of those are in a
different file from this one.

---

## The summary is not the description

**`[ONE-LINE CARD SUMMARY]` earns the click. The post's `meta description` is the SEO line.** They
may differ and often should. The card summary is the teaser.

**Use curly quotes and apostrophes** — " " and ' — to match the rest of the site, not straight ones.
This is the same house rule the post template follows, and a straight quote inside an attribute is
also the thing most likely to end a value early.

---

## What this block depends on, and does not carry

**Every class in it is defined in `blog/index.html`, not here:** `post-card`, `container`,
`post-meta`, `read-link`. A copy-paste publish therefore cannot produce an unstyled card — the
styling is waiting for it at the destination.

**The corollary is the thing to watch:** renaming any of those four classes in `blog/index.html`
breaks every card already in the list *and* this template, and nothing connects them. The
dependency runs one way and is invisible from this end.

---

## What never comes back

| Never | Why |
|---|---|
| A comment, of any kind | that is what this file is; the block ships into the index |
| `<em>` inside `[POST TITLE]` | cards style uniformly; the post's `<h1>` does not |
| Straight quotes in the summary | house style, and they truncate attributes |
| Reusing the post's `meta description` as the summary | different jobs — SEO versus the click |
