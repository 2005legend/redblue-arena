# ShopSphere — Website 2

Your World. Your Products. Your Shopping Experience.

## Current implementation status

This repository currently implements the storefront presentation, **not the complete security lab**. It has 32 catalog entries across six categories, generated product photography, catalog search/filtering/sorting/pagination, product details, in-session cart quantity editing, wishlist, offers, account forms and customer support forms. Cart and favorites survive client navigation, not reloads.

Account, newsletter, support and checkout submissions explicitly report that services are not connected. There are no real orders, stored accounts, database, administrator account, invoices, API endpoints, intentionally vulnerable modules, canary flags or referee yet. Displayed ratings/reviews and catalog entries are presentation fixtures, not persisted customer data. No security scenario is claimed as passing.

## Isolation boundary

The requested architecture is **entirely local-only**, including stored profiles and all ten intentionally vulnerable scenarios. Lovable's application runtime is hosted; localhost in the development sandbox does not make the resulting app local-only. This hosted storefront therefore contains no vulnerable endpoints or canaries, and no hosted database was provisioned. A separate local execution environment is required before backend phases can be completed. Do not deploy a deliberately vulnerable lab publicly. Simulate payments only; never collect real payment information.

## Development

Use Bun with this repository's existing TanStack Start setup:

```sh
bun install
bun run dev --host 127.0.0.1
bunx vitest run src/test/catalog.test.ts src/test/app-routing.test.tsx
```

The frontend uses React 19, TypeScript, TanStack Start/Router, Tailwind v4 and Lucide. Do not replace the router or add Supabase Edge Functions to this hosted application. Shared styling is in `src/styles.css`; shared shell and session state are in `src/components/store-shell.tsx`.

## Verification and outstanding phases

See `roadmap.md` for exact completion status. Catalog tests cover at least 30 unique product identifiers, all six required categories, actual search matching, price/category filters, sorting and new arrivals. Browser checks cover adding a product, editing quantity and subtotal, filtered search, product details, wishlist interaction, and desktop/mobile layouts.

Phases 2–6 require the real isolated backend: database/authentication and roles, persistent commerce, exactly ten actual vulnerable modules/canaries, OpenAPI 3.1, structured logs, deterministic referee and reset/patch regression tests. No demo credentials or fabricated API specification are provided for services that do not exist.

## Git

The current repository is maintained in place. No other project was overwritten. GitHub connection and selecting/creating the `website-2` synced branch must be done in Lovable Project Settings → Git; this agent cannot switch the synced branch or connect an existing repository.
