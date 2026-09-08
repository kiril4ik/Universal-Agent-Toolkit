# Next.js Rules
- Follow the installed Next.js router/version; do not mix Pages/App Router patterns casually.
- Prefer Server Components for server-owned data/markup and Client Components only when browser interactivity requires them.
- Authenticate and authorize server actions/route handlers like public APIs.
- Avoid request waterfalls; start independent I/O early and await together.
- Keep secrets and server-only code out of client bundles.
- Verify current-version caching, image, font, and routing semantics before relying on memory.
