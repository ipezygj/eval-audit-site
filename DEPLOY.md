# Deploy — Measured, Not Believed (eval-integrity site)

Single static file: `index.html`. No build, no dependencies, no server code. Fully self-contained (inline CSS, inline SVG favicon). Works on any static host.

## Fastest path (free, ~3 min) — Netlify Drop
1. Go to **https://app.netlify.com/drop**
2. Drag the whole `eval-audit-site` folder onto the page.
3. You get a live URL instantly (e.g. `random-name.netlify.app`).
4. Site settings → Domain management → add your custom domain.

## Alternative hosts (all free, all fine for one static file)
- **Cloudflare Pages** — connect a GitHub repo OR direct upload. Free SSL, fast CDN. Best if you buy the domain at Cloudflare (one dashboard).
- **GitHub Pages** — push this folder to a repo, Settings → Pages → deploy from branch. URL: `<user>.github.io/<repo>`.
- **Vercel** — `vercel` CLI or drag-drop; instant `*.vercel.app`.

## Custom domain
Recommended: **measurednotbelieved.com** (matches the book + Stripe brand — one name across the whole funnel).
Buy at **Cloudflare Registrar** (~$10/yr, at-cost, free WHOIS privacy) or Namecheap.
Then point it at the host (Netlify/Cloudflare/Vercel all give exact DNS records).

Fallback names if the .com is taken:
- evalintegrity.audit / .dev
- measurednotbelieved.dev
- ilpovaatainen.com (personal, then this page at /audits)

## After the domain is live
1. Update the two CTA links in `index.html` if you add a Stripe Payment Link or a Calendly.
   - Currently: LinkedIn DM + Leanpub book.
   - Add a `Book Spot Check — $600` button pointing at a Stripe Payment Link once the Stripe account exists.
2. Add an OG image later (`og:image` meta) for nicer link previews in DMs/posts.

## One-line local preview
Open `index.html` directly in a browser, or:
`python -m http.server 8000` inside this folder → http://localhost:8000
