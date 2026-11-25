# ShopSphere roadmap

- [x] Phase 1a: Storefront, category/shop/product pages, shared design system, 32 presentation catalog entries, session cart/wishlist, filters/sorting/pagination. Seven automated tests passed; browser verified add-to-cart, quantity/subtotal, product search/details and wishlist. Desktop/mobile reviewed.
- [ ] Phase 1b: Remaining authenticated account, order, invoice and admin views need real local services; current account/support/checkout pages explicitly decline unconnected submissions.
- [ ] Phase 2: Persistent catalog, authentication, profiles/roles, orders, support and admin. Confirmed stored profiles and entirely local-only lab. Blocked on a local backend outside Lovable's hosted runtime; do not silently provision hosted data.
- [ ] Phase 3: Ten isolated backend vulnerabilities and deterministic canaries. Confirmed local-only; blocked on a local execution environment outside hosted application.
- [ ] Phase 4: Actual API specification, structured request logs and agent manifest. Depends on lab backend.
- [ ] Phase 5: Referee, functional/security regression tests and reset fixtures. Depends on backend.
- [ ] Phase 6: Verify real end-to-end shopping and all ten exploit/patch checks; complete setup documentation. Depends on remaining phases.