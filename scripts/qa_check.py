#!/usr/bin/env python3
"""Formatting QA gate for Localize carousel cards.

The spec requires Copy and CTA formatting to be checked with code, never by eye.
Feed it the batch as JSON, either a list of cards or {"cards": [...]}, where each
card is {"Name": ..., "Copy": ..., "CTA": ..., "context": ...}.

    python3 scripts/qa_check.py cards.json
    cat cards.json | python3 scripts/qa_check.py

Exits 0 when every card passes, 1 when any card fails, and prints one line per
violation plus a measurements table.
"""

import json
import re
import sys

SECTION_MAX = 175
CTA_LINE1_MAX = 55
CTA_LINE2_MAX = 45
CTA_TOTAL_MAX = 90

DASHES = "—–"
BULLET_START = re.compile(r"^\s*(?:[-*•‣◦]|#{1,6}\s|\d+[.)]\s)")
EMOJI = re.compile(
    "[\U0001f300-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff⬀-⯿]"
)
URL = re.compile(r"(https?://|www\.|\b[a-z0-9-]+\.(?:com|org|net|gov|edu|io)\b)", re.I)
ATTRIBUTION = re.compile(r"\baccording to\b", re.I)
FILLER = [
    "revolutionary", "game changing", "game-changing", "in today's world",
    "it is important to note", "quietly", "shockingly", "amazingly",
    "incredible", "unbelievable",
]
EXPLAINERS = re.compile(r"\b(because|so that|which means|that's why|thats why)\b", re.I)
# ". " mid-section, ignoring common abbreviations and decimals.
MID_SENTENCE = re.compile(r"(?<![A-Z])(?<!\bNo)(?<!\bSt)(?<!\bMr)(?<!\bMs)(?<!\bDr)"
                          r"(?<!\bSen)(?<!\bRep)(?<!\bJr)(?<!\bSr)(?<!\d)[.!?]\s+(?=[A-Z0-9])")


def split_sections(text):
    return [s.strip() for s in re.split(r"\n\s*\n", text.strip()) if s.strip()]


def check_copy(copy, fail):
    if not copy or not copy.strip():
        fail("Copy is empty")
        return []
    sections = split_sections(copy)
    n = len(sections)
    if n < 2 or n > 4:
        fail(f"Copy has {n} sections, must be 2-4 (3 preferred)")
    if "\n" in copy and not re.search(r"\n\s*\n", copy):
        fail("Copy uses single newlines, sections must be separated by a blank line")
    for i, s in enumerate(sections, 1):
        if len(s) > SECTION_MAX:
            fail(f"Copy section {i} is {len(s)} chars, cap is {SECTION_MAX}")
        if s[-1] in ".!?,;:":
            fail(f"Copy section {i} ends in punctuation ({s[-1]!r})")
        if any(d in s for d in DASHES):
            fail(f"Copy section {i} contains an em or en dash")
        if BULLET_START.match(s):
            fail(f"Copy section {i} starts with a bullet, number or header")
        if EMOJI.search(s):
            fail(f"Copy section {i} contains an emoji")
        if "#" in s:
            fail(f"Copy section {i} contains a hashtag or header mark")
        if URL.search(s):
            fail(f"Copy section {i} contains a URL or domain")
        if ATTRIBUTION.search(s):
            fail(f"Copy section {i} contains an 'according to' attribution")
        if MID_SENTENCE.search(s):
            fail(f"Copy section {i} looks like more than one sentence")
        if "\n" in s:
            fail(f"Copy section {i} contains a line break inside the section")
        low = s.lower()
        for word in FILLER:
            if word in low:
                fail(f"Copy section {i} contains filler word {word!r}")
    return sections


def check_cta(cta, fail):
    if not cta or not cta.strip():
        fail("CTA is empty")
        return None, None
    parts = split_sections(cta)
    if len(parts) != 2:
        fail(f"CTA has {len(parts)} blank-line-separated lines, must be exactly 2")
        return None, None
    line1, line2 = parts

    for label, line in (("CTA line 1", line1), ("CTA line 2", line2)):
        if "\n" in line:
            fail(f"{label} contains an extra line break")
        if line[-1] in ".!?,;:":
            fail(f"{label} ends in punctuation ({line[-1]!r})")
        if "?" in line:
            fail(f"{label} contains a question mark")
        if EMOJI.search(line) or "#" in line:
            fail(f"{label} contains an emoji or hashtag")
        if any(d in line for d in DASHES):
            fail(f"{label} contains an em or en dash")
        if EXPLAINERS.search(line):
            fail(f"{label} contains an explaining word")

    w1, w2 = len(line1.split()), len(line2.split())
    if len(line1) > CTA_LINE1_MAX:
        fail(f"CTA line 1 is {len(line1)} chars, cap is {CTA_LINE1_MAX}")
    if not 3 <= w1 <= 8:
        fail(f"CTA line 1 has {w1} words, must be 3-8")
    if "localize" in line1.lower():
        fail("CTA line 1 contains the word Localize")
    if "near you" in line1.lower():
        fail("CTA line 1 contains 'near you', which belongs to line 2")
    if line1.split()[0] not in ("Support", "Find", "Back"):
        fail(f"CTA line 1 starts with {line1.split()[0]!r}, must be Support, Find or Back")

    if len(line2) > CTA_LINE2_MAX:
        fail(f"CTA line 2 is {len(line2)} chars, cap is {CTA_LINE2_MAX}")
    if not 4 <= w2 <= 8:
        fail(f"CTA line 2 has {w2} words, must be 4-8")
    if line2.lower().count("localize") != 1:
        fail(f"CTA line 2 must contain Localize exactly once, found {line2.lower().count('localize')}")
    if not line2.endswith("Localize"):
        fail(f"CTA line 2 must end on the word Localize, ends on {line2.split()[-1]!r}")

    total = len(line1) + len(line2)
    if total >= CTA_TOTAL_MAX:
        fail(f"CTA is {total} chars across both lines, must be under {CTA_TOTAL_MAX}")
    return line1, line2


def check_name(name, fail):
    if not name or not name.strip():
        fail("Name is empty")
        return
    if any(d in name for d in DASHES):
        fail("Name contains an em or en dash")
    if EMOJI.search(name):
        fail("Name contains an emoji")


def main():
    raw = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()
    data = json.loads(raw)
    cards = data["cards"] if isinstance(data, dict) else data

    total_failures = 0
    for idx, card in enumerate(cards, 1):
        failures = []
        fail = failures.append
        name = card.get("Name", "")
        check_name(name, fail)
        sections = check_copy(card.get("Copy", ""), fail)
        line1, line2 = check_cta(card.get("CTA", ""), fail)
        if not card.get("context", "").strip():
            fail("context is empty, the receipts are required")

        label = (name[:70] + "...") if len(name) > 70 else name
        status = "FAIL" if failures else "pass"
        print(f"[{status}] {idx}. {label}")
        lengths = ", ".join(str(len(s)) for s in sections) or "none"
        print(f"        copy sections: {len(sections)} ({lengths} chars)")
        if line1 is not None:
            print(f"        cta: {len(line1)} + {len(line2)} = {len(line1) + len(line2)} chars, "
                  f"ends on {line2.split()[-1]!r}")
        for f in failures:
            print(f"        - {f}")
        total_failures += len(failures)

    print()
    if total_failures:
        print(f"{total_failures} violation(s) across {len(cards)} card(s). Nothing should be saved.")
        return 1
    print(f"All {len(cards)} card(s) pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
