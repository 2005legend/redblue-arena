"""Big, judge-readable Vibe Arena architecture diagram (PNG) for the README.

Layout is on a strict grid; the script asserts no two boxes overlap, so the
result is always clean without a visual pass.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

W, H = 20.0, 11.0
fig, ax = plt.subplots(figsize=(W, H), dpi=160)
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
fig.patch.set_facecolor("#0b1016")

INK, SUB = "#e6edf3", "#8aa0b4"
RED, RED_BG = "#ff6b6d", "#2a1215"
BLUE, BLUE_BG = "#5aa2ff", "#101c2e"
GREEN, GREEN_BG = "#43d68f", "#0e2419"
AMBER, AMBER_BG = "#f5c518", "#282009"
GREY_BG = "#18202b"

RECTS = []

def box(x, y, w, h, title, lines, edge, fill, tsize=17, lsize=13.2):
    assert (x, y, w, h) not in RECTS
    for (rx, ry, rw, rh) in RECTS:
        olap = x < rx+rw and rx < x+w and y < ry+rh and ry < y+h
        assert not olap, f"OVERLAP at {(x,y,w,h)} vs {(rx,ry,rw,rh)}"
    RECTS.append((x, y, w, h))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.10,rounding_size=0.24",
                                fc=fill, ec=edge, lw=2.6, zorder=3))
    cy = y + h - 0.55
    ax.text(x + w/2, cy, title, ha="center", va="top", color=INK,
            fontsize=tsize, fontweight="bold", zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + w/2, cy - 0.85 - i*0.72, ln, ha="center", va="top", color=SUB,
                fontsize=lsize, zorder=4)

def arrow(x1, y1, x2, y2, color, sub="", gap=0.7, lab_d=(0, 0), lab_fs=12.5):
    # shrink the joint ends so the arrowhead points at the box, not into it
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=30,
                                 lw=3.0, color=color, zorder=5))
    if sub:
        ax.text((x1+x2)/2 + lab_d[0], (y1+y2)/2 + lab_d[1], sub, ha="center", va="center",
                color=color, fontsize=lab_fs, fontstyle="italic", zorder=6,
                bbox=dict(boxstyle="round,pad=0.25", fc="#0b1016", ec="none", alpha=0.85))

# titles
ax.text(W/2, H-0.35, "VIBE ARENA — ARCHITECTURE", ha="center", va="top",
        color=INK, fontsize=30, fontweight="bold")
ax.text(W/2, H-1.10, "an attacker LLM, a defender LLM, and a deterministic referee — fighting over a real FastAPI website",
        ha="center", va="top", color=SUB, fontsize=16)

# ---------------- grid ----------------
C1x, C1w = 0.7, 5.0      # 0.7 .. 5.7
C2x, C2w = 6.5, 5.0      # 6.5 .. 11.5
C3x, C3w = 12.3, 5.0     # 12.3 .. 17.3
C4x, C4w = 18.1, 1.1     # right rail (narrow)

R1y, R1h = 8.45, 1.75    # top row
R2y, R2h = 6.30, 1.80
R3y, R3h = 4.10, 1.80
R4y, R4h = 1.85, 1.75

# ---------------- boxes ----------------
box(C1x, R1y, C1w, R1h, "BUILDER + arena.yaml",
    ["10-line config: app dir, seed DB,", "users, admin routes, loot,", "strategy (hybrid / sweep / llm)"],
    GREY_BG and "#8899aa", GREY_BG, tsize=16, lsize=12.6)

box(C1x, R2y, C1w, R2h, "SANDBOX  (sandbox.py)",
    ["fresh app copy + immutable", "seed.db on port :800x",
     "loot files for traversal,", "psutil tree kill, busy-port skip"],
    "#8899aa", GREY_BG, tsize=16, lsize=12.6)

box(C2x, R2y, C2w, R2h, "TARGET APP  (live)",
    ["FastAPI + SQLite — the real victim", "running inside the arena",
     "demo_shop / Lumen Goods, 11 bugs"],
    RED, RED_BG, tsize=16, lsize=12.6)

box(C3x, R2y, C3w, R2h, "ARENA UI  (React + Vite)",
    ["Red/Blue score, VulnPopup cards", "token counters, dashboards",
     "zero-key --replay for judges"],
    BLUE, BLUE_BG, tsize=16, lsize=12.6)

box(C4x, R2y, C4w, R2h, "", [" ", " ", " "], "#8899aa", GREY_BG)
ax.text(C4x+C4w/2, R2y+R2h-0.9, " spawns", rotation=90, ha="center", va="center", color=SUB, fontsize=11.5)

box(C1x, R3y, C1w, R3h, "RED AGENT  (sweep.py + red.py)",
    ["TIER 1 — template sweep, 0 tokens:", "7 bug classes from /openapi.json",
     "TIER 2 — LLM probes for leftovers", "(budget-capped, host-locked HTTP)"],
    RED, RED_BG, tsize=16, lsize=12.6)

box(C2x, R3y, C2w, R3h, "DETERMINISTIC REFEREE  (no LLM)",
    ["Blue scores only if 100% of the", "frozen tests pass AND the exact", "exploit replay is BLOCKED"],
    GREEN, GREEN_BG, tsize=16, lsize=12.6)

box(C3x, R3y, C3w, R3h, "BLUE AGENT  (blue.py)",
    ["reads breach evidence only,", "narrow files + per-class recipe",
     "writes SEARCH/REPLACE patches", "(never deletes routes / 403-all)"],
    BLUE, BLUE_BG, tsize=16, lsize=12.6)

box(C1x, R4y, C1w, R4h, "VERIFIED PATCH CACHE",
    ["accepted fixes stored by (class, route);", "next match the referee re-verifies", "them on staging — reuse at 0 tokens"],
    AMBER, AMBER_BG, tsize=15.5, lsize=12.2)

box(C2x, R4y, C2w, R4h, "STAGING COPY + fresh DB",
    ["Blue's patch lands here,", "boots on :8010, :8011 …,",
     "every step is verified before swap"],
    "#8899aa", GREY_BG, tsize=16, lsize=12.6)

box(C3x, R4y, C3w, R4h, "EVENT LOG  (events.jsonl)",
    ["every action is a typed event:", "breach, patched, score, health …",
     "streamed over WebSocket /ws"],
    GREEN, GREEN_BG, tsize=15.5, lsize=12.2)

box(C3x, R1y, C3w, R1h, "OUTPUTS",
    ["hardened.patch · report.md", "tests/security/*.py — a permanent", "pytest regression test per exploit"],
    GREEN, GREEN_BG, tsize=16, lsize=12.6)

# ---------------- arrows ----------------
arrow(3.2, R1y-0.02, 3.2, R2y+R2h, "#8899aa", "boot target", lab_d=(1.55, 0))
arrow(5.7+0.02, R2y+R2h/2, 6.5-0.02, R2y+R2h/2, "#8899aa")

# red attacks target (diagonal through empty band y 5.7..6.3)
arrow(3.0, R3y+R3h, 7.4, R2y-0.02, RED, "attacks — real HTTP requests", lab_d=(-2.1, -0.15))

# target -> blue (diagonal through empty band y 5.7..6.3)
arrow(10.4, R2y-0.02, 13.2, R3y+R3h, RED, "breach evidence", lab_d=(-1.05, -0.35))

# blue -> staging (diagonal through gap between C3 and C2 below referee)
arrow(13.6, R3y-0.02, 11.55, R4y+R4h+0.03, BLUE, "patch goes to staging", lab_d=(1.9, 0.0), lab_fs=12.0)

# staging -> referee (vertical)
arrow(9.0, R4y+R4h, 9.0, R3y-0.02, "#8899aa", "verify tests + replay", lab_d=(2.15, 0), lab_fs=12.2)

# referee -> target (vertical, PASS)
arrow(8.0, R3y+R3h, 8.0, R2y-0.02, GREEN, "PASS — swap live target (next port)", lab_d=(2.6, 0), lab_fs=12.4)

# referee -> blue (horizontal, FAIL)
arrow(11.5-0.02, R3y+R3h/2, 12.3+0.02, R3y+R3h/2, "#ff6b6d", "", lab_d=(0,0))
ax.text(11.95, R3y+R3h+0.28, "FAIL — drop patch,\nboot-log feedback", ha="center",
        color="#ff6b6d", fontsize=11.8, fontstyle="italic", zorder=6,
        bbox=dict(boxstyle="round,pad=0.25", fc="#0b1016", ec="none", alpha=0.85))

# referee -> cache (nearly-horizontal segment through the R3/R4 band, then drop into cache top)
arrow(7.4, R3y-0.02, 3.4, R4y+R4h+0.26, AMBER)
arrow(3.4, R4y+R4h+0.24, 3.4, R4y+R4h+0.02, AMBER)

# cache -> red (vertical, 0-token reuse)
arrow(3.2, R4y+R4h, 3.2, R3y-0.02, AMBER, "cache hit — 0-token fix", lab_d=(2.5, 0), lab_fs=12.4)

# event log -> UI: L-path through the empty right band (x 17.3..18.1)
ax.add_patch(FancyArrowPatch((17.3, 4.85), (17.75, 4.85), arrowstyle="-", lw=3.0, color=GREEN, zorder=5))
ax.add_patch(FancyArrowPatch((17.75, 4.85), (17.75, 7.1), arrowstyle="-", lw=3.0, color=GREEN, zorder=5))
arrow(17.75, 7.1, 17.32, 7.1, GREEN)
ax.text(17.93, 5.95, "events stream", rotation=90, ha="center", va="center", color=GREEN,
        fontsize=12.0, fontstyle="italic", zorder=6)

# UI -> outputs (vertical)
arrow(14.9, R2y+R2h, 14.9, R1y-0.02, GREEN, "export deliverables", lab_d=(2.15, 0.15), lab_fs=12.2)

ax.text(W/2, 1.0, "One deterministic rule: Blue only scores when every frozen functional test still passes AND Red's exact exploit is blocked.",
        ha="center", color=SUB, fontsize=15, fontstyle="italic")

fig.savefig(r"C:\Users\USER\sidaarth\compute50 hackathon\vibe-arena\docs\img\architecture.png",
            dpi=160, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.25)
print("saved")
