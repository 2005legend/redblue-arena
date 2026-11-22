"""Builds docs/presentation/vibe-arena.pptx (first draft). Needs: pip install python-pptx"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
BG, FG, ACC, RED, BLUE, MUTED = (RGBColor(0x0B, 0x0E, 0x14), RGBColor(0xE6, 0xEA, 0xF2),
                                 RGBColor(0x6E, 0xE7, 0xA0), RGBColor(0xFF, 0x5D, 0x5D),
                                 RGBColor(0x4D, 0xA3, 0xFF), RGBColor(0x9A, 0xA5, 0xB8))

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
blank = prs.slide_layouts[6]


def slide(title, bullets=(), image=None, accent=ACC):
    s = prs.slides.add_slide(blank)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    tb = s.shapes.add_textbox(Inches(0.7), Inches(0.45), Inches(12), Inches(1.0))
    p = tb.text_frame.paragraphs[0]
    p.text = title
    p.font.size, p.font.bold, p.font.color.rgb = Pt(36), True, accent
    width = Inches(6.4) if image else Inches(12)
    body = s.shapes.add_textbox(Inches(0.7), Inches(1.6), width, Inches(5.3))
    tf = body.text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.text = "• " + b
        para.font.size, para.font.color.rgb = Pt(17 if image else 20), FG
        para.space_after = Pt(12)
    if image:
        s.shapes.add_picture(str(image), Inches(7.3), Inches(1.7), width=Inches(5.6))
    return s


slide("VIBE ARENA", [
    "Red and Blue AI agents attack and fix your app before you ship it",
    "Compute 50 Hackathon - Round 1 - Domain 9: Developer Productivity and Intelligent Automation",
    "Team: (add names)",
])
slide("The problem", [
    "AI tools let anyone build and deploy an app in an evening",
    "Broken access control and injection are among the most common web flaws",
    "Solo builders have no security team and usually no tests",
    "Today they find out when a stranger reads someone else's data",
], accent=RED)
slide("The idea", [
    "RED attacks a sandboxed copy of your app as a normal user",
    "BLUE reads the evidence and writes a source-code fix",
    "A REFEREE with no AI verifies: every normal-user test still passes AND the exact attack now fails",
    "You get a hardened patch, a report, and a new security test per exploit",
])
slide("Prior work (and what we add)", [
    "RvB (arXiv 2601.19726): red/blue loop with regression-tested patches",
    "OpenAI Daybreak (Nov 2026): enterprise pentest and patch drafting, waitlist",
    "DARPA AIxCC (2025): autonomous find-and-patch on open-source C/Java",
    "We build on these ideas and aim them at builders with no tests and no security team",
], accent=BLUE)
slide("What is new", [
    "Works with zero existing tests: captures a functional suite first, human-approved, then freezes it",
    "Every exploit becomes a permanent regression test in your repo",
    "Runs on a free or cheap API key, fully local",
    "A watchable arena that makes security understandable",
])
slide("How it works", [
    "Each app copy runs on its own port with its own database copy",
    "Red can only reach the sandbox (enforced in code)",
    "Blue returns SEARCH/REPLACE edits; the .patch is built by difflib",
    "Fix is verified on a staging copy, then swapped in",
    "4 bug classes: SQL injection, IDOR, admin bypass, path traversal",
], image=ROOT / "docs" / "img" / "arena-midmatch.jpg")
slide("Results", [
    "(Fill in after the live pilot - do not invent numbers)",
    "Exploits found per class, fixes verified, time to patch, tokens per match",
    "Negative control: an AI-generated shop app that came out secure - the referee reports no wins",
], accent=ACC)
slide("Safety, limits, next steps", [
    "Attacks only a local sandbox; a human reviews the diff before anything ships",
    "Limits: FastAPI targets so far; 4 bug classes",
    "Next: Node/Express targets, a CI gate before merge, shadow mode on real traffic",
], accent=BLUE)

out = ROOT / "docs" / "presentation" / "vibe-arena.pptx"
prs.save(out)
print("saved", out, len(prs.slides.__iter__.__self__._sldIdLst), "slides")
