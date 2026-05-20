# RNVizion Portfolio Site

A single-page personal portfolio for Christian Smith. Built with vanilla HTML/CSS/JS — no build step, no dependencies.

## Local Preview

Just open `index.html` in your browser. That's it.

For a slightly nicer dev experience with live reload, you can use any static server:

```bash
# Python (already installed on most systems)
python -m http.server 8000

# Then open http://localhost:8000
```

## Adding Your Screenshots

Drop PNG or JPG screenshots into the `assets/` folder with these exact filenames:

- `assets/text-transformer.png`
- `assets/color-palette-manager.png`
- `assets/color-picker.png`
- `assets/icon-builder.png`
- `assets/color-mixer.png`

Recommended size: **1200×900px** (4:3 aspect ratio). If the file is missing, a placeholder text will show instead.

## Deploying to GitHub Pages

1. Create a new repo on GitHub named `rnvizion.github.io` (must match your username exactly)
2. Push this folder's contents to the repo's `main` branch
3. Go to repo Settings → Pages → set Source to "Deploy from a branch" → branch `main` → folder `/ (root)`
4. Wait ~1 minute. Your site is live at `https://rnvizion.github.io`

## Custom Domain (Optional)

If you want something like `christiansmith.dev`:

1. Buy the domain (Namecheap, Google Domains, Porkbun — usually $10–15/year)
2. In repo Settings → Pages → Custom domain, enter your domain
3. Configure your domain's DNS to point to GitHub Pages (4 A records + 1 CNAME — instructions in GitHub Pages settings)

## Updating Content

Everything is in `index.html`. Search for the section you want to edit (HERO, ABOUT, PROJECTS, etc.) and update the text. No build step required.
