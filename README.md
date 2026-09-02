# Localize Daily Idea Engine

A daily automation that feeds the Localize carousel pipeline. Once a day it researches
fresh, verifiable food-sovereignty stories, checks them against everything the brand has
already published, writes the headline, Copy and CTA, and creates finished cards on the
**Ideas** tab of the Master Carousels Notion database.

It merges what used to be two separate Claude projects, the Carousel Headline Engine and
the Localize Copy & CTA Writer, into one unattended pass: ideate, verify, dedupe, write,
save.

## How it runs

A Claude Routine fires a fresh session on a daily schedule. That session has no memory of
yesterday, so the whole spec travels in the prompt itself. It ends with 10 new cards in
Notion and a written summary of what it wrote, what it killed and why.

## The loop

1. The engine writes cards to the Ideas tab with no `Date`, no `File` and `Archive`
   unchecked, which is exactly the Ideas view's filter.
2. A human assigns `Page`, `Template`, `Design` and `Date`, which moves the card off the
   Ideas tab onto a real content calendar.
3. Or a human checks `Archive`, which rejects it.
4. The next run reads both signals back out of the Master table and steers accordingly.

Archiving the misses is the whole feedback mechanism. It costs one checkbox and it is what
keeps the batches from drifting.

## Files

| File | What it is |
| --- | --- |
| `docs/daily-idea-engine.md` | The full spec: target, dedupe protocol, headline, Copy, CTA and QA rules |
| `docs/routine-prompt.md` | The exact self-contained prompt installed in the Routine |
| `scripts/qa_check.py` | The formatting QA gate, run over the batch before anything is saved |

## Dedupe

The Master table is the log of every idea the brand has ever had, used or unused, and it is
in the thousands of rows. Reading it whole on every run is not practical, so the engine
uses four slice queries for orientation (recent work, archived work, recent CTAs, and the
BANG headlines as pattern seeds) and then a targeted `LIKE` query per candidate on that
story's distinctive tokens: the place, the person, the company, the statute number, the
crop.

Same event, same subject, same mechanism is a kill. The same topic with a different place,
actor, mechanism, or a documented new development is a fresh angle and ships.

## QA gate

Copy and CTA formatting is checked with code, never by eye:

```bash
python3 scripts/qa_check.py cards.json
```

Where `cards.json` is a list of `{"Name", "Copy", "CTA", "context"}` objects. It prints
per-card measurements and exits non-zero on any violation.

## Tuning

- **Batch size** and **lane rotation** live in the Routine prompt, mirrored in
  `docs/routine-prompt.md`.
- **Schedule** is the Routine's cron expression, stored in UTC.
- Change either by editing the Routine, then updating `docs/routine-prompt.md` to match.
