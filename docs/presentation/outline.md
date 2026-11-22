# Slide outline (8 slides)

1. **Title:** Vibe Arena: Red vs Blue AI agents that attack and fix your app before you ship. Team names, Domain 9.
2. **The problem:** AI-built apps ship fast; broken access control and injection are common; solo builders have
   no security team and no tests.
3. **Idea in one picture:** Red attacks, Blue patches, referee verifies (diagram with arrows between the three).
4. **Prior work (be honest):** RvB (arXiv 2601.19726), OpenAI Daybreak (Nov 2026, enterprise), DARPA AIxCC
   (2025, open-source C/Java), CAI attack/defence CTFs. "We build on these."
5. **What is new:** for builders with no tests (we capture a test suite first, human-approved); every exploit
   becomes a permanent regression test; works with a free API key; a watchable arena.
6. **How it works:** sandbox per port with its own DB copy, host-locked Red tools, Blue SEARCH/REPLACE edits
   verified on a staging copy, deterministic referee. Screenshot of the arena.
7. **Results:** pilot numbers once measured (exploits found, fixes verified, time to patch, tokens). Until then
   do not invent numbers. Include the negative-control result on targets/shop_app.
8. **Safety, limits, next steps:** local sandbox only; a human reviews the diff; limits: FastAPI only so far,
   4 bug classes; next: Node/Express targets, CI gate, shadow mode.
