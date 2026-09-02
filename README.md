# Localize Daily Idea Engine

A daily automation that feeds the Localize carousel pipeline. Once a day it researches
fresh, verifiable food-sovereignty stories, checks them against everything the brand has
already published, writes the headline, Copy and CTA, and creates finished cards on the
**Ideas** tab of the Master Carousels Notion database.

It merges what used to be two separate Claude projects, the Carousel Headline Engine and
the Localize Copy & CTA Writer, into one unattended pass: ideate, verify, dedupe, write,
save.

## How it runs

Two modes share one pipeline.

**Seed-driven, on demand (primary).** Paste a headline that already worked into a Claude
Project carrying `docs/project-instructions.md`, and it returns 25 to 50 fresh, verified
cards built on the same nerve, written straight into the Notion Ideas tab. This is the mode
in use.

**Autonomous daily (paused).** A Claude Routine that fires a fresh session on a schedule,
picks its own lane by weekday, and writes 10 cards. Its schedule is currently disabled; the
Routine still exists and can be re-enabled or fired by hand. Its prompt lives in
`docs/routine-prompt.md`.

Both modes use the same gates, the same ledger, and the same QA rules.

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
| `docs/project-instructions.md` | Seed-driven project instructions, the mode in use: paste a headline, get 25 to 50 cards |
| `docs/routine-prompt.md` | The self-contained prompt installed in the paused daily Routine |
| `scripts/qa_check.py` | The formatting QA gate, run over the batch before anything is saved |
| `docs/run-log.md` | What each run shipped, what the dedupe gate killed, and which lanes are worked out |

The engine's run memory is not in the repo, because a scheduled session clones the default
branch and would not see it. It lives in Notion as the
[Localize Idea Ledger](https://app.notion.com/p/3cf2ea3539fb81cd8964e820a19b840f), which is
also editable by hand: adding a line under Burned Subjects keeps the engine off that story
for good.

## Dedupe, and why it is also the cost design

The Master table is the log of every idea the brand has ever had, used or unused, and it
runs to thousands of rows. The first run proved how mined it is: 16 of 26 researched
candidates turned out to already be in there.

Three gates run in front of the research, in this order, cheapest first.

**Gate A, within the batch**, collapses candidates that tell the same story as each other.
On a 45-card run the model writes 120-plus candidate lines in one sitting and some of them
converge without it noticing. Free, and the gate most often forgotten.

**Gate B, the ledger**, is a Notion page the engine reads at the start of every run and
appends to at the end. It holds a census of which lanes are saturated, a list of burned subjects, and
every subject the engine has shipped. It matches on the *story*, so it catches a collision
even when the wording shares nothing, which a text search never will. It also replaces the
old habit of pulling 435 raw headlines a day just to re-derive what had been covered.

It also carries a Seeds already run log, so handing the engine the same seed headline twice
does not produce the same batch twice.

**Gate C, the `LIKE` backstop**, covers the thousands of older rows that predate the ledger. Two or
three genuinely distinctive tokens per candidate — a surname, an organization, a statute
number, an unusual crop — batched into one query with a `LIMIT`. Never a bare state or
country: on the first run `%michigan%` matched about a hundred rows, truncated, and settled
nothing.

In both, same event with the same subject and mechanism is a kill. The same topic with a
different place, actor, mechanism, or a documented new development is a fresh angle and
ships.

If the ledger cannot be read, the run stops rather than proceeding on the backstop alone.

Only what survives all three gates gets researched, capped at roughly two searches per card. Candidate lines are nearly free; verified stories are expensive. Generating
40 candidates cold and throwing most away costs far less than verifying 26 and discarding
16 of them.

## Keeping usage down

The levers, in rough order of how much they save:

1. **Never research before the gates.** This is the whole design. Reordering it is the one
   change that would quietly triple the cost of a run.
2. **Keep the ledger current.** Step 13 of the routine appends to it. A run that skips that
   step still ships good cards but leaves the next run with no memory.
3. **Narrow dedupe tokens, always with a `LIMIT`.** Broad tokens cost a lot to read and
   settle nothing.
4. **Short `context` fields**, about 80 words. Notion echoes the full payload back on write,
   so long ones are paid for twice.
5. **Archive the misses.** It costs one checkbox and it is the only signal that stops the
   engine spending research on a direction you do not want.

The model is a further lever and is deliberately left alone: the Routine runs on whatever it
was created with, and changing it is a judgment call about quality, not something to change
silently. Most of a run is searching, verifying and writing to a strict format, which a
smaller model handles well; headline judgment is the part that rewards the larger one. The
honest way to decide is to run a week on each and compare how many cards get assigned
versus archived.

## QA gate

Copy and CTA formatting is checked with code, never by eye:

```bash
python3 scripts/qa_check.py cards.json
```

Where `cards.json` is a list of `{"Name", "Copy", "CTA", "context"}` objects. It prints
per-card measurements and exits non-zero on any violation.

## The Notion connector

The Routine fires a fresh session each day, and that session needs Notion to read the
Master log and write the cards. The Routine itself stores no explicit connector grant,
because this workspace does not allow attaching one through the API. That turned out not to
matter: a probe session spawned fresh in the same environment loaded and called Notion
tools successfully, so the environment supplies them.

If a daily run ever reports that it cannot reach Notion, that is the thing to check first,
and the fix is to attach the Notion connector to the Routine in the claude.ai Routines UI.

## Tuning

- **Batch size** and **lane rotation** live in the Routine prompt, mirrored in
  `docs/routine-prompt.md`.
- **Schedule** is the Routine's cron expression, stored in UTC.
- Change either by editing the Routine, then updating `docs/routine-prompt.md` to match.
