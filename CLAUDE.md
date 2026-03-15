# CLAUDE.md - Reading Tracker (読書トラッカーβ)

## Project Overview

A client-side Japanese reading tracker web app built with Next.js. Users can add books (via Amazon URLs or search), track reading status, rate books, set reading goals, and view analytics. All data is stored in localStorage — there is no backend.

## Tech Stack

- **Framework:** Next.js 16 (App Router) with React 19
- **Language:** TypeScript 5 (strict mode)
- **Styling:** Tailwind CSS 4 (utility classes only, no component libraries)
- **Linting:** ESLint 9 with next/core-web-vitals + TypeScript config

## Project Structure

```
src/
├── app/                  # Next.js App Router (page.tsx is the main entry)
│   ├── page.tsx          # Main dashboard — book list, backfill logic, state management
│   ├── layout.tsx        # Root layout (lang="ja", Geist fonts)
│   └── globals.css       # Global styles + Tailwind imports
├── components/           # All React components ("use client")
│   ├── AmazonUrlInput.tsx    # Amazon URL parsing & ISBN-based book fetch
│   ├── BookCard.tsx          # Book display card with status/rating
│   ├── BookForm.tsx          # Add/edit modal form (uses BookSearch)
│   ├── BookSearch.tsx        # Google Books search dropdown (debounced)
│   ├── Dashboard.tsx         # Genre pie chart + reading stats
│   ├── DataManager.tsx       # JSON export/import for backup
│   ├── NearbyBookstoreMap.tsx # Geolocation + Google Maps embed
│   ├── ReadingJournal.tsx    # Monthly reading calendar
│   ├── StarRating.tsx        # 5-star rating input
│   ├── StatusTabs.tsx        # Tab navigation for book statuses
│   └── TsundokuPop.tsx       # Daily random unread book recommendation
├── lib/                  # Utility modules
│   ├── amazon.ts         # Amazon URL parsing, ASIN/ISBN extraction
│   ├── google-books.ts   # Google Books API client + category mapping
│   ├── openbd.ts         # OpenBD API (Japanese ISBN lookups, no key needed)
│   ├── storage.ts        # localStorage CRUD with migration logic
│   └── goals.ts          # Reading goals & journal date management
└── types/
    └── book.ts           # Book interface, status types, genre constants
```

## Commands

```bash
npm run dev      # Start dev server (port 3000)
npm run build    # Production build
npm run start    # Run production build
npm run lint     # Run ESLint (eslint .)
```

## Key Conventions

### Code Style
- All components use `"use client"` directive (client-side only app)
- Functional components with hooks — no class components
- Tailwind utility classes for all styling (no CSS modules, no styled-components)
- Color palette: zinc (neutral), indigo/violet (primary), amber (accent), emerald (success)
- All UI text is in Japanese

### TypeScript
- Strict mode enabled — no `any` types
- Path alias: `@/*` maps to `./src/*`
- Book status is a union type: `"tsundoku" | "reading" | "finished" | "wishlist"`
- 34 Japanese genre categories defined in `types/book.ts`

### Data Storage
- All data lives in localStorage under keys:
  - `reading-tracker-books` — book collection
  - `reading-tracker-goal` — yearly reading target
  - `reading-tracker-journal` — daily reading log
- Migration logic in `storage.ts` handles deprecated fields (`publishedYear` → `publishedDate`, `unread` → `tsundoku`)

### External APIs
- **Google Books API** — search and metadata (requires `NEXT_PUBLIC_GOOGLE_BOOKS_API_KEY` env var)
- **OpenBD API** — Japanese ISBN lookups (free, no key required)
- **Google Maps** — embedded bookstore finder (uses geolocation)

### Performance Patterns
- Backfill routine runs once per day (localStorage cooldown)
- Google Books rate-limited to 30 books/session with custom `RateLimitError` class
- 7-day skip cache for books where API lookups return no data
- BookSearch input debounced at 400ms
- `useMemo` for genre filtering and tsundoku selection

## Testing

No automated test setup exists. Changes should be verified manually via `npm run dev` and by running `npm run build` to catch type errors. Always run `npm run lint` before committing.

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `NEXT_PUBLIC_GOOGLE_BOOKS_API_KEY` | Optional | Google Books API access (search + metadata) |
