# Localize Daily Idea Engine — full spec

One job, run once a day, unattended: find viral-grade carousel stories that Localize has
not already run, verify them, write the headline, Copy and CTA, and drop each one into the
**Ideas** tab of the Master Carousels database as a finished card.

Nothing here is assigned to a page, a template, a designer, or a date. A human does that
afterward, and that act is what moves a card off the Ideas tab onto a real calendar. If a
human checks **Archive** instead, that card was repetitive or not good enough, and that is
the feedback signal for the next run.

---

## Target

| Thing | Value |
| --- | --- |
| Database | Master Carousels |
| Database URL | `https://app.notion.com/p/1462ea3539fb837abdeb811a692b0ea9` |
| Data source | `collection://cf22ea35-39fb-829f-9432-07370ec52bcb` |
| Ideas view (destination) | `https://app.notion.com/p/1462ea3539fb837abdeb811a692b0ea9?v=3cb2ea3539fb809b9264000c5e04a0e5` |
| Master view (dedupe log) | `https://app.notion.com/p/1462ea3539fb837abdeb811a692b0ea9?v=9e92ea3539fb83569d7008616bdb00f0` |
| Ledger page (run memory) | `https://app.notion.com/p/3cf2ea3539fb81cd8964e820a19b840f` |
| Batch size | 10 cards per run |

The Ideas view is the Master table filtered to `Date` is empty **and** `File` is empty
**and** `Archive` is unchecked. A new page that sets none of those three lands on the Ideas
tab automatically. There is no separate Ideas database, so every card written here is also
in the Master log the moment it is created.

### Fields to write

Exactly four, exact casing:

- `Name` — the headline (title property)
- `Copy` — the carousel middle slides
- `CTA` — the final slide
- `context` — the receipts: what was verified, where it came from, and anything left out

### Fields to never touch

`Date`, `File`, `Page`, `Template`, `Design`, `Designer Notes`, `Caption`, `Performance`,
`posted`, `ready`, `Archive`.

Setting `Date` or `File` would pull the card straight off the Ideas tab, and `Page`,
`Template` and `Design` are human assignments. Leave all of them empty.

Never edit an existing row. This engine only creates.

---

## Step 1 — Load memory, cheaply

The Master table holds thousands of rows and cannot be read whole on every run. Earlier
versions of this spec pulled 435 raw headlines a day to re-derive what had been covered.
The ledger page replaces that. Four reads, no more.

**1a. The ledger.** `notion-fetch` the ledger page. It carries the saturated-lane census,
the burned subjects, and every subject this engine has shipped. This is the primary dedupe
memory, and unlike a text search it matches on the story rather than the wording.

**1b. New rows in the last three days**, which catches anything a human added and any
verdict they passed:

```sql
SELECT "Name", "Archive" FROM "collection://cf22ea35-39fb-829f-9432-07370ec52bcb"
WHERE date(createdTime) >= date('now','-3 days') LIMIT 60
```

**1c. Recent rejections**, the feedback signal:

```sql
SELECT "Name" FROM "collection://cf22ea35-39fb-829f-9432-07370ec52bcb"
WHERE "Archive" = '__YES__' AND date(createdTime) >= date('now','-45 days') LIMIT 30
```

**1d. Recent CTAs**, so the Localize line does not repeat:

```sql
SELECT "CTA" FROM "collection://cf22ea35-39fb-829f-9432-07370ec52bcb"
WHERE "CTA" IS NOT NULL AND "CTA" <> '' ORDER BY createdTime DESC LIMIT 15
```

Anything archived in 1c that came from a recent run of this engine is a direct verdict on
its own work. Read it as such.

Occasionally, when the ledger looks stale, also pull the BANG headlines
(`WHERE "Performance" = 'BANG' ORDER BY "date:Date:start" DESC LIMIT 20`) to re-calibrate
on the phrasing that actually landed. Skip it on ordinary days. A lot of the old archive is
raw brainstorm stubs from before this pipeline existed rather than considered rejections,
so weight recent archives far more heavily than old ones.

---

## Step 2 — Pick the lanes for today

Rotate so consecutive days do not feel like the same batch. By weekday, weight the batch
toward these lanes and fill the rest from anywhere in the territory:

- **Monday** — laws, mandates, ballot measures, court rulings on food and land
- **Tuesday** — cities and regions that learned to feed themselves
- **Wednesday** — ordinary people versus an authority over growing or selling food
- **Thursday** — industrial food exposed: contamination, consolidation, labeling, recalls
- **Friday** — people and places doing it differently: co-ops, butcher shops, farm-direct
- **Saturday** — food history, forgotten practice, heritage seed and breed
- **Sunday** — the odd lane: invasive species eaten, unlikely crops, strange programs

Full topic territory: food sovereignty, local food systems, self-production, and walking
away from industrial food. Within that, laws and mandates; cities that fed themselves
through a crisis; front-yard and backyard garden fights; regions banning industrial inputs;
co-operative and farm-to-table systems; seed, land and ag-policy events with a clear before
and after; invasive species turned into food; celebrity and athlete farms; contamination
and corporate-consolidation stories.

Aim for a batch that ranges. Never ship ten cards from one lane.

---

## Step 3 — Generate cold, with no searching at all

Write out about 40 candidate story ideas from the model's own knowledge. One line each: the
subject, the place, roughly when, and the reversal. **No web search in this step.**

This ordering is the whole efficiency design. The first run of this engine researched and
verified candidates and then discovered that 16 of 26 were already in the table, which
means most of the research spend bought nothing. Candidate lines are nearly free; verified
stories are expensive. Generate cheap, filter hard, then research only what survives.

Bias hard toward where fresh material actually lives, because the table is deeply mined and
most obvious American candidates will collide:

- International stories over American ones
- Anything before 1970 over anything recent
- News from the last two weeks, which by definition cannot be in the table yet
- The lanes the ledger marks Open over the ones it marks Saturated

---

## Step 4 — Gate against the ledger (free)

Drop every candidate whose subject appears in the ledger's Burned Subjects or Covered
Subjects. Match on the story, not the wording: the same event told differently is the same
event. This filter costs nothing beyond the read already done in Step 1, so be aggressive.
Expect to lose about a third of the candidates here.

---

## Step 5 — Gate against the Master table (cheap)

The ledger only knows what has passed through it. The Master table holds thousands of older
rows, so a text backstop still matters for those.

For each remaining candidate pick two or three genuinely distinctive tokens: a person's
surname, an organization, a statute number, an unusual crop or organism, a small place
name. **Never a bare US state, country, or common word.** On the first run, `%michigan%`
returned about a hundred rows, hit the truncation limit, and settled nothing. Broad tokens
are both useless and expensive.

Batch every candidate's tokens into one or two queries and cap the result:

```sql
SELECT "Name", "Archive" FROM "collection://cf22ea35-39fb-829f-9432-07370ec52bcb"
WHERE lower("Name") LIKE '%tukirin%' OR lower("Name") LIKE '%kokopelli%'
   OR lower("Name") LIKE '%nganjuk%'
LIMIT 25
```

Read the hits and rule:

- **Same event, same subject, same mechanism → kill it.** Rewording a headline is not a new
  idea.
- **Same topic, different story → keep it.** A different place, a different actor, a
  different mechanism, or a documented new development in a story the brand covered before
  is a fresh angle. Kalamazoo's garden fight is not Miami Shores' garden fight.
- **A hit that was archived → treat that subject as burned** unless the new angle is
  clearly the thing the archived one was missing, and say so in `context`.

---

## Step 6 — Research only the survivors

Now, and only now, use web search. Work down the survivor list until 10 fully verify, then
stop searching. Budget roughly two searches per card and about 25 for the whole run. If a
candidate does not verify in two searches, drop it and take the next survivor rather than
chasing it.

A card ships only if it is a real, specific event, place, law, program or person, confirmed
by research rather than recalled from memory, and carries a genuine reversal or shock
rather than merely being topical. A dropped idea is always better than an invented one.
Never soften an unverifiable story into a hypothetical.

---

## Step 7 — Write the headline

Shock setup plus a curiosity loop. Common shapes:

- `X did [surprising thing] and it [dramatic consequence]`
- `[Place] [did the unthinkable], until [twist]`
- `Everyone said [common belief], then [place] proved them wrong`
- `[Authority] tried to stop [ordinary person], so [escalation]`

Rules: no em dashes, no bullets, no opinion adjectives doing the work the facts should do
(amazing, shocking, incredible). Let the real event carry the charge. Capitalizing a word
or two for emphasis is fine where it sharpens the hook. No curiosity bait like "but here is
the craziest part."

The headline is a contract with the reader. Whatever fact hooked them, the Copy delivers on
it first.

---

## Step 8 — Write the Copy

The Copy is the middle of the carousel. Slide 1 is the headline, the last slide is the CTA,
and these sections are everything between. Write them as a short news brief that walks the
reader through the story the way a wire-service lede does. Not a caption. Not a pitch.

**Structure**

- 3 sections is the sweet spot. Drop to 2 only if the material is genuinely thin. Go to 4
  only if the story needs a fourth beat. Never 5.
- One sentence per section. It can be long and carry a clause or two, but it is one
  sentence.
- Sections separated by a blank line (double newline).
- **Hard cap 175 characters per section.** Target zone is roughly 100 to 160. Count
  programmatically, never by eye. Do not pad a dense short section to reach the ceiling.
- No period or other trailing punctuation at the end of a section.
- No bullets, numbering, headers, emojis, hashtags, em dashes or en dashes.

**Arc** (guidance, not a template)

One section carries the core fact, finding or conflict behind the headline with the
specifics attached. One connects that fact to something real: health, ecosystems, farmers,
livelihoods, trust in the food system. One can gesture toward local, transparent or
farmer-direct food as the better path, but only where the facts support it. Reorder and
combine freely. Do not let every card in a run come out the same shape.

Where a story is procedural, name the exact status and never overstate it: proposed, filed,
advanced, passed one chamber, signed, enjoined, ruled, settled, dismissed, pending. Where a
story is a mechanism, put the mechanism in plain words and keep a biological mechanism
distinct from a proven clinical outcome. Where a story is a business or a person, state
ownership accurately: owner versus investor versus endorser, current versus former.

**Voice**

- Strictly neutral. It reads like a news article stating facts. Any lean lives in which
  story got picked and which facts led, never in the wording.
- Do not restate or paraphrase the headline. Explain, deepen, extend.
- No citations, URLs, domains or "according to" attributions in the Copy. A named
  institution or researcher who is part of the story is fine.
- No hype and no filler: revolutionary, game changing, in today's world, it is important to
  note, quietly, shockingly, amazingly, actually, really, just, incredible, tiny, very.
- Plain everyday words over technical, legal or industry jargon.
- This audience is sharply averse to anything that reads as machine written. No stock
  transitions, no "not X but Y" constructions, no rhetorical questions, no three-item
  rhythm repeated across sections.

**Reference examples of the target voice**

```
Traditionally the Maasai of Kenya and Tanzania live on raw milk, meat and blood from their cattle, supplemented with local plants and almost nothing processed

In the 1960s, a Vanderbilt researcher studied 400 Maasai men eating a diet that was 66% fat and found almost none had high cholesterol or heart disease

They also lean on dozens of local herbs like osokonoi and olkinyei for digestion and immunity, plants studied for real antiviral and antimicrobial effects

When Maasai men moved to cities and switched to more refined diets, their health markers plummeted
```

```
University of Tokyo research shows red nets are significantly more effective than traditional black or white netting at deterring pests

The bright color acts as a natural deterrent, as insects are unable to perceive red and instinctively avoid it

Field trials found crops covered by red netting required 25-50% less pesticide than uncovered fields
```

```
Mike Lewis is a Kentucky veteran who founded the Growing Warriors Project in 2012 after his brother returned from eight tours in Afghanistan with a brain injury

The program began with 10 veteran families and now trains veterans on a 500 acre Kentucky farm with support networks across the country

Lewis believes farming gives veterans purpose and healing, something he witnessed watching his wounded brother find peace in the soil
```

**Do not use existing cards in the database as a style reference.** Much of what is in there
predates this spec: bullet-style Copy, five sections, CTAs running past 90 characters, CTAs
with Localize mid-sentence, CTAs arguing a thesis. Some of those cards are rated BANG, and
that rating is about the headline, not the copy. This spec is the only style authority.

---

## Step 9 — Write the CTA

The final slide. **Two small thoughts, on two lines, blank line between them.** Nothing
else. It relates to the post but never explains the post.

```
Line 1   who to support or find, in the language of this post
         (blank line)
Line 2   the Localize line
```

**Line 1 — the ask**

- Plain imperative, starting with `Support` or `Find`, occasionally `Back`.
- Points at the kind of producer in the post: dairy farmers, ranchers, homesteaders raising
  eggs and pork, "these producers". Optionally one plain brand value word already in the
  vocabulary, such as `food freedom`.
- **Never contains the word Localize.** Never contains "near you", which belongs to line 2.
- 3 to 8 words, hard cap 55 characters.
- Not a fact, not a stat, not a quote, not a setup line, not a thesis.

**Line 2 — the Localize line**

- The only place the word Localize appears, and it says one thing: Localize is how you find
  them near you.
- **Hard rule: `Localize` is the final word.** No exceptions, however well an alternative
  reads.
- 4 to 8 words, hard cap 45 characters.
- Word it fresh. Check the CTAs pulled in Step 1c and avoid whatever ran most recently.
  Within a batch, rotate through the working set in order so a phrasing never lands near
  itself.

Working set to draw from and vary off:

```
Find them on Localize
Find them near you with Localize
See them near you with Localize
You can see them near you with Localize
Find yours on Localize
The ones near you are on Localize
See who is near you on Localize
Find the closest ones on Localize
Find the ones near you on Localize
See the ones near you on Localize
Look for them near you on Localize
Find them in your area on Localize
See them in your area on Localize
The closest ones are on Localize
Find them close to home on Localize
See what is near you on Localize
Find who is near you on Localize
Your local ones are on Localize
```

**Both lines**

- No trailing period or any end punctuation. No comma splice on a second clause.
- No explaining words: because, so that, which means, that's why.
- No question marks, emojis, hashtags, em dashes.
- Never "Click the link", "Sign up now", "Download the app", or generic marketing.
- Whole CTA under 90 characters across both lines.
- Saved with a real blank line between the two lines.

**Good**

```
Support these producers

Find them on Localize
```

```
Support dairy farmers and food freedom

Find them near you with Localize
```

**Bad**, one line doing both jobs:

```
Find farmers and food freedom advocates near you with Localize
```

**Bad**, a thesis stacked in front of the ask:

```
Football pays the bills for a few years, land and cattle pay a family for generations. Find ranchers building the long game with Localize
```

---

## Step 10 — Write the context field

`context` is the receipts, written for a human who wants to spot-check before scripting.
Keep it to about 80 words. Notion echoes the whole payload back on write, so long
context fields are paid for twice. Plain text, four short parts:

- The verified spine of the story: who, where, when, and the fact that makes it true.
- Source names, and links where available. Reputable news organizations; court opinions,
  legislation, filings, agency notices; USDA, FDA, CDC, NIH, FAO, EPA, state agencies,
  county records, university extensions, peer-reviewed studies; official first-party sites;
  established trade publications with clear sourcing.
- Never as primary evidence: Reddit, Wikipedia, unverified social posts, meme pages,
  reposted screenshots, SEO farms, content mills, tabloid speculation, "studies show"
  summaries without the study, or search snippets alone.
- Any claim deliberately left out of the Copy because it could not be confirmed.
- The dedupe note: which tokens were checked and why this angle is fresh.

---

## Step 11 — QA gate, run on every card before saving

**Factual.** Every sentence supported by a credible source. No claim exceeds its source.
Dates, numbers, company names, legal status and current affiliations correct. No association
stated as causation, no implied medical treatment or cure, no unsupported motive. The Copy
does not contradict or quietly correct the headline. The CTA does not overclaim.

If the headline itself does not survive verification, do not write Copy that quietly
corrects it and do not write Copy vague enough to dodge the problem. Drop the card, pull a
replacement from the reserve pool, and note the kill in the summary.

**Formatting, checked with code and never by eye.** Run `scripts/qa_check.py` over the batch:

```bash
python3 scripts/qa_check.py cards.json
```

It exits non-zero and names every violation. A card that fails is rewritten and rechecked.
Never save a failing card.

**Voice.** Reads like a straight news brief. No filler adjectives, no marketing language, no
press-release voice, no unexplained jargon. Carries real researched specifics. Specific
enough that it could not be pasted onto a different story unchanged.

---

## Step 12 — Write into Notion

`notion-create-pages` against
`data_source_id: cf22ea35-39fb-829f-9432-07370ec52bcb`, setting only `Name`, `Copy`, `CTA`
and `context`. Write in small groups and verify each group landed before continuing. Leave
the page body empty; everything lives in properties.

If a write fails, retry once, then report the failure with that card's headline rather than
moving on silently.

---

## Step 13 — Update the ledger

This is what makes tomorrow's run cheap. Do not skip it.

`notion-update-page` on the ledger page with `command: "insert_content"` and
`position: {"type": "end"}`, appending:

- One line per shipped card under Covered Subjects: `- YYYY-MM-DD, subject and place, mechanism`
- One line per candidate killed in Step 5 under Burned Subjects: `- subject, already in Master`
- One line per candidate that failed verification: `- subject, did not verify, what was wrong`

Keep each line short. If the census in the ledger is more than about a month old, refresh it
while you are there.

A run that skips this step still produces good cards, but it hands the next run no memory
and the cost savings evaporate.

---

## Step 14 — Summary

Close every run with:

- Cards written: headline and Notion link, one line each.
- Candidates killed at the dedupe gate, with the row they collided with.
- Candidates killed at verification, with what was found and what was wrong.
- Any claim deliberately left out of a Copy for lack of confirmation.
- Anything worth a human double-check: shaky sourcing, a procedural status that could still
  change, an event date that may pass.

---

## Tuning

- **Batch size** — change the number in the Target block of the routine prompt.
- **Lanes** — edit the weekday rotation in Step 2.
- **Schedule** — the routine's cron expression, stored in UTC.
- **Feedback** — archive the cards that miss. The next run reads the archive and steers off
  them.
